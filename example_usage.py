"""
Example: Amazon Account Creation with HeroS MS Phone Verification
Demonstrates best practice for using AmazonCreator with HeroSMSPhoneManager in multi-threaded environment.
"""

import threading
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from hidemium import Hidemium
from herosms import HeroSMS
from phonemanager import HeroSMSPhoneManager
from AmazonCreator import AmazonCreator


# ==================== CONFIGURATION ====================

# HeroSMS API Configuration
HEROSMS_API_KEY = "YOUR_HEROSMS_API_KEY"
SERVICE_CODE = "am" # Amazon
COUNTRY_CODE = 6     # USA
POOL_SIZE = 5        # Keep 5 phones in pool
MAX_PHONE_USES = 2   # Each phone used max 2 times

# Thread Configuration
THREAD_COUNT = 3     # Run 3 threads concurrently


# ==================== WORKER FUNCTION ====================

def worker_thread(thread_id, phone_manager):
	"""
	Worker function that creates one Amazon account.
	
	Args:
		thread_id: Unique thread identifier
		phone_manager: Shared HeroSMSPhoneManager instance (thread-safe)
	"""
	thread_name = f"Thread-{thread_id}"
	print(f"[{thread_name}] Starting...")
	
	hidemium = Hidemium()
	driver = None
	
	try:
		# 1. Open Hidemium profile
		# Assume you have profiles with UUIDs
		profile_uuid = f"your-profile-uuid-{thread_id}"
		result = hidemium.open_profile(uuid=profile_uuid)
		
		if not result:
			print(f"[{thread_name}] Failed to open profile")
			return
		
		# Parse result (adjust based on your hidemium.open_profile return format)
		# Assuming it returns something like "OK:remote_port:execute_path"
		parts = result.split(':')
		remote_port = parts[1]
		execute_path = parts[2]
		
		# 2. Setup Selenium WebDriver
		options = webdriver.ChromeOptions()
		options.binary_location = execute_path
		options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
		
		driver = webdriver.Chrome(options=options)
		wait = WebDriverWait(driver, 15)
		
		print(f"[{thread_name}] Browser connected")
		
		# 3. Create AmazonCreator WITH phone_manager (Best Practice!)
		amazon = AmazonCreator(driver, wait, phone_manager=phone_manager)
		
		# 4. Run the main flow (includes email + phone verification)
		result = amazon.main_flow(thread_name)
		
		if result['status'] == 'success':
			print(f"[{thread_name}] ✅ SUCCESS: {result['message']}")
		else:
			print(f"[{thread_name}] ❌ FAILED: {result['message']}")
			
	except Exception as e:
		print(f"[{thread_name}] ❌ ERROR: {e}")
		
	finally:
		# Cleanup
		if driver:
			try:
				driver.quit()
			except:
				pass
		
		try:
			hidemium.close_profile(uuid=profile_uuid)
		except:
			pass


# ==================== MAIN EXECUTION ====================

def main():
	"""
	Main function: Setup shared PhoneManager and run multiple threads
	"""
	print("=" * 60)
	print("Amazon Account Creator with HeroSMS")
	print("=" * 60)
	
	# 1. Initialize HeroSMS client
	print("\n[SETUP] Initializing HeroSMS client...")
	hero_client = HeroSMS(api_key=HEROSMS_API_KEY)
	
	# Check balance
	balance = hero_client.get_balance()
	if balance['status'] == 'success':
		print(f"[SETUP] HeroSMS Balance: ${balance['balance']:.2f}")
	else:
		print(f"[SETUP] ⚠️  Could not check balance: {balance.get('message')}")
	
	# 2. Create SHARED PhoneManager (one instance for all threads)
	print(f"\n[SETUP] Creating shared PhoneManager (pool size: {POOL_SIZE})...")
	phone_manager = HeroSMSPhoneManager(
		hero_client=hero_client,
		service=SERVICE_CODE,
		country=COUNTRY_CODE,
		pool_size=POOL_SIZE,
		max_uses=MAX_PHONE_USES,
		timeout_seconds=300  # 5 minutes timeout
	)
	
	print(f"[SETUP] PhoneManager ready: {phone_manager.get_stats()}")
	
	# 3. Create and start worker threads
	print(f"\n[SETUP] Starting {THREAD_COUNT} worker threads...")
	print("=" * 60)
	
	threads = []
	for i in range(THREAD_COUNT):
		t = threading.Thread(
			target=worker_thread,
			args=(i, phone_manager),  # Pass shared phone_manager
			name=f"Worker-{i}"
		)
		threads.append(t)
		t.start()
	
	# 4. Wait for all threads to complete
	print("\n[MAIN] Waiting for all threads to complete...")
	for t in threads:
		t.join()
	
	# 5. Print final statistics
	print("\n" + "=" * 60)
	print("FINAL STATISTICS")
	print("=" * 60)
	stats = phone_manager.get_stats()
	for key, value in stats.items():
		print(f"{key}: {value}")
	
	print("\n✅ All workers completed!")


# ==================== ALTERNATIVE: WITHOUT PHONE VERIFICATION ====================

def main_without_phone():
	"""
	Example: Without phone verification (phone_manager=None)
	"""
	def worker_no_phone(thread_id):
		thread_name = f"Thread-{thread_id}"
		hidemium = Hidemium()
		
		# ... setup driver ...
		
		# AmazonCreator WITHOUT phone_manager
		amazon = AmazonCreator(driver, wait, phone_manager=None)
		
		# Phone verification will be skipped automatically
		result = amazon.main_flow(thread_name)
		
		# ... cleanup ...
	
	threads = []
	for i in range(3):
		t = threading.Thread(target=worker_no_phone, args=(i,))
		threads.append(t)
		t.start()
	
	for t in threads:
		t.join()


# ==================== RUN ====================

if __name__ == "__main__":
	# Run with phone verification
	main()
	
	# Or run without phone verification
	# main_without_phone()
