import threading, time, os
from hidemium import Hidemium
from herosms import HeroSMS
from phonemanager import HeroSMSPhoneManager
from logger import Logger
from ctypes import c_bool
from multiprocessing import Value
from toolhelper import ToolHelper
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from amazoncreator import AmazonCreator

logger = Logger()

# ==================== CONFIGURATION ====================
HEROSMS_API_KEY = "d17feec2b014cfAd9c4c8b2685d39c00"  # Thay bằng API key thật
SERVICE_CODE = "am"  # Amazon
COUNTRY_CODE = 73     # Brazil
POOL_SIZE = 3       # Pool size cho phone numbers
MAX_PHONE_USES = 2   # Mỗi phone dùng tối đa 2 lần


def worker_thread(thread_id, stop_flag, position, phone_manager,proxy=None):
	thread_name = f"Thread-{thread_id}"
	hidemium = Hidemium()
	driver = None
	uuid = None
	try:
		while not stop_flag.value:
			try:
				# 1. Create and open profile
				logger.warning(f"{thread_name} Creating profile...")
				uuid = hidemium.create_profile_by_default(33296)
				if not uuid:
					logger.error(f"{thread_name} Failed to create profile")
					break
				# 2. Open profile with proxy (optional)
				logger.warning(f"{thread_name} Opening profile {uuid}...")
				remote_port, execute_path = hidemium.open_profile(
					uuid=uuid,
					proxy="SOCKS5|127.0.0.1|60001" # Optional
				)
				# 3. Setup Selenium
				options = webdriver.ChromeOptions()
				options.binary_location = execute_path
				options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
				driver = webdriver.Chrome(options=options)
				wait = WebDriverWait(driver, 15)
				logger.warning(f"{thread_name} Browser connected")
				# 4. Navigate to Amazon
				driver.get('https://www.amazon.com/')
				time.sleep(3)
				# 5. Create AmazonCreator with shared phone_manager (Best Practice!)
				amazon = AmazonCreator(driver, wait, phone_manager=phone_manager)
				# 6. Run main flow (email + phone verification)
				logger.warning(f"{thread_name} Starting account creation flow...")
				result = amazon.main_flow(thread_name)
				if result['status'] == 'success':
					logger.success(f"{thread_name} ✅ Account created successfully!")
				else:
					logger.error(f"{thread_name} ❌ Account creation failed: {result['message']}")
				# 7. Cleanup
				if driver:
					driver.quit()
					driver = None
				if uuid:
					hidemium.close_profile(uuid)
					uuid = None
				break
			except Exception as e:
				logger.error(f"{thread_name} Error in worker: {e}")
				if driver:
					try:
						driver.quit()
					except:
						pass
					driver = None
				if uuid:
					try:
						hidemium.close_profile(uuid)
					except:
						pass
					uuid = None
				break
	except KeyboardInterrupt:
		logger.error(f"⛔ {thread_name} stopped by user.")
	finally:
		if driver:
			try:
				driver.quit()
			except:
				pass
		if uuid:
			try:
				hidemium.close_profile(uuid)
			except:
				pass
def main():
	"""Main function with shared HeroSMSPhoneManager"""
	logger.warning('=' * 60)
	logger.warning('AMAZON CREATOR WITH HIDEMIUM + HEROSMS VER 2.0')
	logger.warning('=' * 60)
	
	# 1. Get thread count
	threads_count = int(logger.input_green("Nhập số luồng muốn chạy: "))
	logger.success('--------------------------------------------------')
	
	# 2. Initialize HeroSMS client
	logger.warning("Initializing HeroSMS client...")
	hero_client = HeroSMS(api_key=HEROSMS_API_KEY)
	
	# Check balance
	balance = hero_client.get_balance()
	if balance['status'] == 'success':
		logger.success(f"HeroSMS Balance: ${balance['balance']:.2f}")
	else:
		logger.warning(f"Could not check balance: {balance.get('message', 'Unknown error')}")
	
	# 3. Create SHARED PhoneManager (ONE instance for ALL threads)
	logger.warning(f"Creating shared PhoneManager (pool size: {POOL_SIZE})...")
	phone_manager = HeroSMSPhoneManager(
		hero_client=hero_client,
		service=SERVICE_CODE,
		country=COUNTRY_CODE,
		pool_size=POOL_SIZE,
		max_uses=MAX_PHONE_USES,
		max_price=0.03,
		timeout_seconds=300
	)
	
	logger.success(f"PhoneManager ready: {phone_manager.get_stats()}")
	logger.success('--------------------------------------------------')
	
	# 4. Setup positions
	toolhelper = ToolHelper()
	positions = toolhelper.generator_positions(threads_count)
	
	# 5. Create stop flag
	stop_flag = Value(c_bool, False)
	thread_list = []
	
	# 6. Start threads
	for i in range(threads_count):
		t = threading.Thread(
			target=worker_thread,
			args=(i + 1, stop_flag, positions[i], phone_manager),  # Pass shared phone_manager
			daemon=True
		)
		t.start()
		thread_list.append(t)
		time.sleep(1)  # Small delay between thread starts
	
	# 7. Wait for threads
	try:
		logger.success(f"✅ {threads_count} threads running. Press Ctrl+C to stop...")
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logger.error("⛔ Ctrl+C received. Stopping threads...")
		stop_flag.value = True
		
		# Wait for all threads to finish
		for t in thread_list:
			t.join(timeout=10)
		
		logger.success("✅ All threads stopped.")
	
	# 8. Final statistics
	logger.warning('=' * 60)
	logger.warning('FINAL PHONE MANAGER STATISTICS')
	logger.warning('=' * 60)
	stats = phone_manager.get_stats()
	for key, value in stats.items():
		logger.warning(f"{key}: {value}")
	logger.warning('=' * 60)


# def main_single_test():
# 	"""
# 	Single thread test mode (for debugging)
# 	Uncomment in __main__ to use
# 	"""
# 	logger.warning('SINGLE THREAD TEST MODE')
# 	logger.success('--------------------------------------------------')
	
# 	# 1. Setup HeroSMS
# 	hero_client = HeroSMS(api_key=HEROSMS_API_KEY)
# 	phone_manager = HeroSMSPhoneManager(
# 		hero_client=hero_client,
# 		service=SERVICE_CODE,
# 		country=COUNTRY_CODE,
# 		pool_size=1,
# 		max_uses=2
# 	)
	
# 	# 2. Setup browser
# 	logger.warning("Creating Hidemium instance...")
# 	hidemium = Hidemium()
	
# 	uuid = "4bd8c03a-7d04-496a-b998-ad20ec3fe63c"  # Use existing profile for testing
# 	logger.warning(f"Opening profile: {uuid}...")
	
# 	try:
# 		remote_port, execute_path = hidemium.open_profile(uuid)
# 		logger.success(f"Profile opened! Port: {remote_port}, Path: {execute_path}")
# 	except Exception as e:
# 		logger.error(f"Failed to open profile: {e}")
# 		return
	
# 	logger.warning("Setting up Chrome driver...")
# 	options = webdriver.ChromeOptions()
# 	options.binary_location = execute_path
# 	options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
	
# 	try:
# 		driver = webdriver.Chrome(options=options)
# 		wait = WebDriverWait(driver, 15)
# 		logger.success("Chrome driver connected!")
# 	except Exception as e:
# 		logger.error(f"Failed to connect driver: {e}")
# 		return
	
# 	# 3. Run
# 	logger.warning("Starting Amazon flow...")
# 	amazon = AmazonCreator(driver, wait, phone_manager=phone_manager)
# 	result = amazon.main_flow("Test-Thread")
	
# 	logger.warning(f"Result: {result['message']}")
	
	# 4. Cleanup
	# driver.quit()
	# hidemium.close_profile(uuid)


if __name__ == "__main__":
	# Run multi-threaded mode
	main()
	
	# Or run single test mode (for debugging)
	# main_single_test()
