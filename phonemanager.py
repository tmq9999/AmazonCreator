import threading
import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class PhoneInfo:
	"""Stores metadata for each phone number"""
	number: str
	used_count: int = 0  # How many times this phone was used (max = 2)
	locked_by: Optional[str] = None  # Thread ID currently using this phone
	locked_at: Optional[datetime] = None  # When the phone was locked
	activation_id: Optional[str] = None  # HeroSMS activation ID
	activation_data: Optional[Dict] = None  # Full activation data from HeroSMS


class PhoneManager:
	"""
	Thread-safe phone number manager for concurrent account registration.
	
	Features:
	- Each phone can be used up to 2 times total
	- Only one thread can use a phone at any moment
	- Automatic timeout handling for crashed workers
	- Thread-safe acquire/release operations
	
	Thread Safety:
	- Uses threading.Lock for all state mutations
	- Uses threading.Condition for efficient waiting
	- All public methods are atomic operations
	"""
	
	def __init__(self, phone_numbers: List[str], timeout_seconds: int = 300):
		"""
		Initialize PhoneManager with a list of phone numbers.
		
		Args:
			phone_numbers: List of phone numbers to manage
			timeout_seconds: Auto-release timeout (default: 5 minutes)
		"""
		# Core data structure: phone_number -> PhoneInfo
		self._phones: Dict[str, PhoneInfo] = {
			phone: PhoneInfo(number=phone) for phone in phone_numbers
		}
		
		# Thread synchronization primitives
		self._lock = threading.Lock()  # Protects all state
		self._condition = threading.Condition(self._lock)  # For efficient waiting
		
		# Configuration
		self._timeout = timedelta(seconds=timeout_seconds)
		
		# Statistics (thread-safe via lock)
		self._total_acquired = 0
		self._total_released = 0
	
	def acquire_phone(self, thread_id: Optional[str] = None, max_wait_seconds: int = 30) -> Optional[str]:
		"""
		Acquire an available phone number for this thread.
		
		Thread Safety:
		- Acquires lock before checking/modifying phone state
		- Uses condition variable to wait efficiently
		- Atomic check-and-set operation
		
		Args:
			thread_id: Unique identifier (auto-detected if None)
			max_wait_seconds: Maximum time to wait for a phone (default: 30s)
		
		Returns:
			Phone number if available, None if timeout or no phones available
		"""
		if thread_id is None:
			thread_id = threading.current_thread().name
		
		print(f"[DEBUG ACQUIRE START] {thread_id} - Function entered, about to acquire condition lock")
		end_time = time.time() + max_wait_seconds
		
		print(f"[DEBUG ACQUIRE] {thread_id} - Attempting 'with self._condition:'...")
		with self._condition:  # Auto-acquires lock
			print(f"[DEBUG] {thread_id} entered acquire_phone, checking for available phones...")
			while True:
				# 1. Release any timed-out phones
				self._release_timed_out_phones()
				
				# 2. Find an available phone
				print(f"[DEBUG] {thread_id} calling _find_available_phone...")
				phone_number = self._find_available_phone()
				print(f"[DEBUG] {thread_id} _find_available_phone returned: {phone_number}")
				
				if phone_number:
					# 3. Lock the phone to this thread
					phone = self._phones[phone_number]
					phone.locked_by = thread_id
					phone.locked_at = datetime.now()
					
					self._total_acquired += 1
					print(f"[DEBUG] {thread_id} successfully acquired phone: {phone_number}")
					return phone_number
				
				# 4. No phone available - wait or timeout
				remaining_time = end_time - time.time()
				print(f"[DEBUG] {thread_id} no phone found, remaining time: {remaining_time:.2f}s")
				if remaining_time <= 0:
					print(f"[DEBUG] {thread_id} timeout, returning None")
					return None
				
				# Wait for a phone to be released (or timeout)
				# Other threads will notify when they release phones
				print(f"[DEBUG] {thread_id} waiting for phone...")
				self._condition.wait(timeout=min(remaining_time, 1.0))
	
	def release_phone(self, phone_number: str, thread_id: Optional[str] = None, success: bool = True) -> bool:
		"""
		Release a phone number and optionally increment its usage count.
		
		Thread Safety:
		- Validates thread ownership before release
		- Atomic increment of usage count
		- Notifies waiting threads
		
		Args:
			phone_number: The phone number to release
			thread_id: The thread that currently owns this phone (auto-detected if None)
			success: If True, increment used_count (default: True)
			         Set to False if registration failed and phone can be reused
		
		Returns:
			True if released successfully, False if validation failed
		"""
		if thread_id is None:
			thread_id = threading.current_thread().name
		
		with self._condition:
			if phone_number not in self._phones:
				return False
			
			phone = self._phones[phone_number]
			
			# Validate ownership
			if phone.locked_by != thread_id:
				return False
			
			# Release the lock
			phone.locked_by = None
			phone.locked_at = None
			
			# Increment usage counter only if registration succeeded
			if success:
				phone.used_count += 1
			
			self._total_released += 1
			
			# Notify waiting threads that a phone is available
			self._condition.notify_all()
			
			return True
	
	def get_stats(self) -> Dict:
		"""
		Get current statistics (thread-safe).
		
		Returns:
			Dictionary with usage statistics
		"""
		with self._lock:
			total_phones = len(self._phones)
			available = sum(1 for p in self._phones.values() 
			                if p.used_count < 2 and p.locked_by is None)
			locked = sum(1 for p in self._phones.values() if p.locked_by is not None)
			exhausted = sum(1 for p in self._phones.values() if p.used_count >= 2)
			
			return {
				'total_phones': total_phones,
				'available': available,
				'locked': locked,
				'exhausted': exhausted,
				'total_acquired': self._total_acquired,
				'total_released': self._total_released
			}
	
	# ==================== PRIVATE METHODS ====================
	# These are called only when lock is already held
	
	def _find_available_phone(self) -> Optional[str]:
		"""
		Find a phone that:
		- Has been used < 2 times
		- Is not currently locked
		
		Must be called with lock held.
		"""
		for phone_number, phone in self._phones.items():
			# Skip exhausted phones early
			if phone.used_count >= 2:
				continue
			if phone.locked_by is None:
				return phone_number
		return None
	
	def _release_timed_out_phones(self):
		"""
		Auto-release phones that have been locked for too long.
		This handles cases where a worker thread crashes.
		
		Must be called with lock held.
		"""
		now = datetime.now()
		
		for phone in self._phones.values():
			# Skip already exhausted phones
			if phone.used_count >= 2:
				continue
			
			if phone.locked_by and phone.locked_at:
				if now - phone.locked_at > self._timeout:
					# Force release - phone was likely used
					print(f"[PhoneManager] Auto-releasing phone {phone.number} "
					      f"(locked by {phone.locked_by} for {now - phone.locked_at})")
					phone.locked_by = None
					phone.locked_at = None
					phone.used_count += 1  # 🔴 CRITICAL: Count as used
					self._condition.notify_all()  # 🔴 CRITICAL: Wake waiting threads


# ==================== HEROSMS INTEGRATION ====================

class HeroSMSPhoneManager(PhoneManager):
	def __init__(self, hero_client, service: str, country: int, 
	             pool_size: int = 5, max_uses: int = 2, 
	             operator: Optional[str] = None, max_price: Optional[float] = None,
	             timeout_seconds: int = 300):
		# Initialize with empty phone list
		super().__init__([], timeout_seconds)
		
		# HeroSMS configuration
		self.hero_client = hero_client
		self.service = service
		self.country = country
		self.pool_size = pool_size
		self.max_uses = max_uses
		self.operator = operator
		self.max_price = max_price
		
		# Activation ID tracking
		self._activation_map: Dict[str, str] = {}  # phone -> activation_id
		
		# Pre-fetch initial pool
		self._refill_pool()
	
	def _refill_pool(self):
		# DO NOT use 'with self._condition:' here - already locked by caller!
		# Count how many we need
		available_count = sum(1 for p in self._phones.values() 
		                     if p.used_count < self.max_uses and p.locked_by is None)
		
		needed = self.pool_size - available_count
		
		if needed <= 0:
			return
		
		print(f"[HeroSMSPhoneManager] Refilling pool: need {needed} phones")
		
		# Fetch new numbers
		for i in range(needed):
			try:
				result = self.hero_client.get_number_v2(
					service=self.service,
					country=self.country,
					operator=self.operator,
					max_price=self.max_price
				)
				
				if result['status'] == 'success':
					phone_number = result['phoneNumber']
					activation_id = str(result['activationId'])
						
					# Add to pool
					self._phones[phone_number] = PhoneInfo(
						number=phone_number,
						activation_id=activation_id,
						activation_data=result
					)
					
					self._activation_map[phone_number] = activation_id
					
					print(f"[HeroSMSPhoneManager] Acquired: {phone_number} (ID: {activation_id})")
				else:
					print(f"[HeroSMSPhoneManager] Failed to get number: {result.get('message', 'Unknown')}")
					break
					
			except Exception as e:
				print(f"[HeroSMSPhoneManager] Error fetching number: {e}")
				break
	
	def acquire_phone(self, thread_id: Optional[str] = None, max_wait_seconds: int = 30) -> Optional[str]:
		if thread_id is None:
			thread_id = threading.current_thread().name
		
		end_time = time.time() + max_wait_seconds
		
		with self._condition:
			while True:
				# 1. Try to refill pool
				self._refill_pool()
				
				# 2. Release timed-out phones
				self._release_timed_out_phones()
				
				# 3. Find available phone
				phone_number = self._find_available_phone()
				
				if phone_number:
					phone = self._phones[phone_number]
					phone.locked_by = thread_id
					phone.locked_at = datetime.now()
					
					# Mark activation as ready in HeroSMS
					if phone.activation_id:
						try:
							self.hero_client.set_status(phone.activation_id, 1)  # Status 1 = Ready
						except Exception as e:
							print(f"[HeroSMSPhoneManager] Failed to set status: {e}")
					
					self._total_acquired += 1
					return phone_number
				
				# 4. Wait or timeout
				remaining_time = end_time - time.time()
				if remaining_time <= 0:
					return None
				
				self._condition.wait(timeout=min(remaining_time, 1.0))
	
	def release_phone(self, phone_number: str, thread_id: Optional[str] = None, success: bool = True) -> bool:
		if thread_id is None:
			thread_id = threading.current_thread().name
		
		with self._condition:
			if phone_number not in self._phones:
				return False
			
			phone = self._phones[phone_number]
			
			# Validate ownership
			if phone.locked_by != thread_id:
				return False
			
			# Update HeroSMS activation status
			if phone.activation_id:
				try:
					if success:
						# Complete activation (status 6)
						self.hero_client.set_status(phone.activation_id, 6)
						print(f"[HeroSMSPhoneManager] Completed activation: {phone.activation_id}")
					else:
						# Cancel activation (status 8)
						self.hero_client.set_status(phone.activation_id, 8)
						print(f"[HeroSMSPhoneManager] Canceled activation: {phone.activation_id}")
				except Exception as e:
					print(f"[HeroSMSPhoneManager] Failed to update activation: {e}")
			
			# Release the lock
			phone.locked_by = None
			phone.locked_at = None
			
			# Increment usage counter only if success
			if success:
				phone.used_count += 1
			
			self._total_released += 1
			
			# Notify waiting threads
			self._condition.notify_all()
			
			return True
	
	def get_sms_code(self, phone_number: str, max_retries: int = 30, retry_interval: int = 10) -> Optional[str]:
		with self._lock:
			if phone_number not in self._phones:
				return None
			
			phone = self._phones[phone_number]
			activation_id = phone.activation_id
		
		if not activation_id:
			print(f"[HeroSMSPhoneManager] No activation ID for {phone_number}")
			return None
		
		print(f"[HeroSMSPhoneManager] Waiting for SMS code (ID: {activation_id})...")
		
		for attempt in range(max_retries):
			try:
				status = self.hero_client.get_status(activation_id)
				print(f"[DEBUG] Attempt {attempt + 1}/{max_retries}, API response: {status}")
				
				if status['status'] == 'success' and status.get('code'):
					code = status['code']
					print(f"[HeroSMSPhoneManager] Got  code: {code}")
					return code
				elif status['status'] == 'wait':
					print(f"[HeroSMSPhoneManager] Waiting... ({attempt + 1}/{max_retries})")
					time.sleep(retry_interval)
				elif status['status'] == 'canceled':
					print(f"[HeroSMSPhoneManager] Activation was canceled")
					return None
				else:
					print(f"[HeroSMSPhoneManager] Unexpected status: {status}")
					time.sleep(retry_interval)  # Continue instead of return
					
			except Exception as e:
				print(f"[HeroSMSPhoneManager] Error checking status: {e}")
				time.sleep(retry_interval)
		
		print(f"[HeroSMSPhoneManager] Timeout waiting for code")
		return None


# ==================== EXAMPLE USAGE ====================

def worker_thread(phone_manager: PhoneManager, task_count: int):
	thread_id = threading.current_thread().name
	
	for i in range(task_count):
		print(f"[{thread_id}] Requesting phone...")
		
		# 1. Acquire a phone (thread_id auto-detected)
		phone = phone_manager.acquire_phone(max_wait_seconds=30)
		
		if not phone:
			print(f"[{thread_id}] No phone available, stopping.")
			break
		
		print(f"[{thread_id}] Got phone: {phone}")
		
		registration_success = False
		try:
			# 2. Simulate registration process
			time.sleep(2)  # Simulate work
			registration_success = True
			
			print(f"[{thread_id}] Registration complete for {phone}")
			
		finally:
			# 3. Release with success flag (thread_id auto-detected)
			success = phone_manager.release_phone(phone, success=registration_success)
			if success:
				print(f"[{thread_id}] Released phone: {phone} (counted: {registration_success})")
			else:
				print(f"[{thread_id}] Failed to release phone: {phone}")


def main():
	"""Example: Static phone list"""
	# 1. Initialize phone manager with 5 phones
	phones = ["+1234567890", "+1234567891", "+1234567892", "+1234567893", "+1234567894"]
	manager = PhoneManager(phones, timeout_seconds=60)
	
	print(f"=== Starting with {len(phones)} phones ===")
	print(f"Stats: {manager.get_stats()}\n")
	
	# 2. Create 10 worker threads (each will do 2 registrations)
	threads = []
	for i in range(10):
		t = threading.Thread(
			target=worker_thread,
			args=(manager, 2),  # No manual thread_id needed
			name=f"Worker-{i}"  # Auto-detected by PhoneManager
		)
		threads.append(t)
		t.start()
	
	# 3. Wait for all threads to complete
	for t in threads:
		t.join()
	
	# 4. Print final statistics
	print(f"\n=== Final Statistics ===")
	stats = manager.get_stats()
	for key, value in stats.items():
		print(f"{key}: {value}")
	
	print(f"\n=== All workers completed! ===")


def main_herosms():
	"""Example: HeroSMS integration"""
	from herosms import HeroSMS
	
	# 1. Initialize HeroSMS client
	api_key = "YOUR_API_KEY"
	hero_client = HeroSMS(api_key)
	
	# 2. Create HeroSMS phone manager
	manager = HeroSMSPhoneManager(
		hero_client=hero_client,
		service='am',      # Amazon
		country=6,         # USA
		pool_size=3,       # Keep 3 phones in pool
		max_uses=2,        # Each phone used max 2 times
		timeout_seconds=300
	)
	
	print("=== HeroSMS Phone Manager Started ===")
	print(f"Stats: {manager.get_stats()}\n")
	
	# 3. Example: Acquire and use a phone
	phone = manager.acquire_phone()
	if phone:
		print(f"Got phone: {phone}")
		
		# Simulate sending verification request
		print("Sending verification request...")
		time.sleep(2)
		
		# Wait for SMS code
		code = manager.get_sms_code(phone, max_retries=10, retry_interval=5)
		
		if code:
			print(f"SUCCESS! Code: {code}")
			manager.release_phone(phone, success=True)
		else:
			print("FAILED to get code")
			manager.release_phone(phone, success=False)
	
	print(f"\nFinal stats: {manager.get_stats()}")


if __name__ == "__main__":
	# Run static example
	main()
	
	# Uncomment to run HeroSMS example
	# main_herosms()