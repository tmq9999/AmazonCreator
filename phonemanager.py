import threading
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class PhoneInfo:
	"""Stores metadata for each phone number"""
	number: str
	used_count: int = 0  # How many times this phone was used (max = 2)
	locked_by: Optional[str] = None  # Thread ID currently using this phone
	locked_at: Optional[datetime] = None  # When the phone was locked


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
		
		end_time = time.time() + max_wait_seconds
		
		with self._condition:  # Auto-acquires lock
			while True:
				# 1. Release any timed-out phones
				self._release_timed_out_phones()
				
				# 2. Find an available phone
				phone_number = self._find_available_phone()
				
				if phone_number:
					# 3. Lock the phone to this thread
					phone = self._phones[phone_number]
					phone.locked_by = thread_id
					phone.locked_at = datetime.now()
					
					self._total_acquired += 1
					return phone_number
				
				# 4. No phone available - wait or timeout
				remaining_time = end_time - time.time()
				if remaining_time <= 0:
					return None
				
				# Wait for a phone to be released (or timeout)
				# Other threads will notify when they release phones
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


# ==================== EXAMPLE USAGE ====================

def worker_thread(phone_manager: PhoneManager, task_count: int):
	"""
	Example worker that simulates account registration.
	Thread ID is auto-detected from threading.current_thread().name
	
	Args:
		phone_manager: Shared PhoneManager instance
		task_count: Number of registrations to perform
	"""
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


if __name__ == "__main__":
	main()