import time, random, requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from logger import Logger
from toolhelper import ToolHelper
from faker import Faker
from selenium.webdriver.support.ui import Select
logger = Logger()
class AmazonCreator:
	
	def __init__(self, driver, wait, phone_manager=None):
		self.driver = driver
		self.wait = wait
		self.phone_manager = phone_manager  # Shared instance for thread-safe phone management
	def continue_captcha(self, max_attempts=5):
		for attempt in range(1, max_attempts + 1):
			try:
				button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//button[normalize-space()="Continue shopping"]')))
				button.click()
				return {'status': 'success','message': 'Clicked Continue shopping'}
			except TimeoutException:
				return {'status': 'skipped','message': 'Continue shopping button not found'}
			except Exception as e:
				if attempt == max_attempts:
					return {'status': 'error','message': f'continue_captcha failed after {max_attempts} attempts: {e}'}
				time.sleep(2)
	def create_account(self, email, full_name, password):
		try:
			input_email = self.wait.until(EC.presence_of_element_located((By.ID, 'ap_email_login')))
			input_email.clear()
			input_email.send_keys(email)
		except TimeoutException:
			return {'status': 'error','message': 'Email input not found'}
		except Exception as e:
			return {'status': 'error','message': f'input_email failed: {e}'}
		time.sleep(random.randint(3,5))
		try:
			button = self.wait.until(EC.element_to_be_clickable((By.ID, 'continue')))
			button.click()
		except TimeoutException:
			return {'status': 'error','message': 'Continue button not found'}
		except Exception as e:
			return {'status': 'error','message': f'button continue failed: {e}'}
		time.sleep(random.randint(2,3))
		#Looks like you're new to Amazon
		try:
			headers = self.driver.find_elements(By.XPATH,'//h1[contains(normalize-space(), "new to Amazon")]')
			if headers:
				button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]')))
				button.click()
		except TimeoutException:
			return {'status': 'error','message': 'Submit button not found'}
		except Exception as e:
			return {'status': 'error','message': f'button submit failed: {e}'}
		time.sleep(random.randint(2,3))
		try:
			input_your_name = self.wait.until(EC.presence_of_element_located((By.ID, 'ap_customer_name')))
			input_your_name.clear()
			input_your_name.send_keys(full_name)
		except TimeoutException:
			return {'status': 'error','message': 'Your name input not found'}
		except Exception as e:
			return {'status': 'error','message': f'input_your_name failed: {e}'}
		time.sleep(random.randint(1,3))
		try:
			input_password = self.wait.until(EC.presence_of_element_located((By.ID, 'ap_password')))
			input_password.clear()
			input_password.send_keys(password)
		except TimeoutException:
			return {'status': 'error','message': 'Password input not found'}
		except Exception as e:
			return {'status': 'error','message': f'input_password failed: {e}'}
		time.sleep(random.randint(1,3))
		try:
			input_re_password = self.wait.until(EC.presence_of_element_located((By.ID, 'ap_password_check')))
			input_re_password.clear()
			input_re_password.send_keys(password)
		except TimeoutException:
			return {'status': 'error','message': 'Re-password input not found'}
		except Exception as e:
			return {'status': 'error','message': f'input_re_password failed: {e}'}
		time.sleep(random.randint(1,3))
		try:
			button = self.wait.until(EC.element_to_be_clickable((By.ID, 'continue')))
			button.click()
		except TimeoutException:
			return {'status': 'error','message': 'Continue button not found'}
		except Exception as e:
			return {'status': 'error','message': f'button continue failed: {e}'}
		return {'status': 'success','message': f'create_account success'}

	def captcha_solving(self):
		"""
		Handle Amazon captcha:
		- Detect Arkose Labs (hard block)
		- Handle normal captcha
		- Skip only when REALLY no captcha
		"""

		# =========================
		# 1️⃣ Detect Arkose Labs
		# =========================
		try:
			self.wait.until(
				EC.frame_to_be_available_and_switch_to_it(
					(By.ID, 'cvf-aamation-challenge-iframe')
				)
			)

			if self.driver.find_elements(By.ID, 'aacb-arkose-elements'):
				return {
					'status': 'blocked',
					'message': 'Arkose Labs challenge detected'
				}

		except TimeoutException:
			# iframe Arkose không xuất hiện → tiếp tục check captcha thường
			pass
		except Exception as e:
			return {
				'status': 'error',
				'message': f'Arkose detection error: {e}'
			}
		finally:
			try:
				self.driver.switch_to.default_content()
			except:
				pass

		# =========================
		# 2️⃣ Check captcha thường
		# =========================
		has_normal_captcha = self.driver.find_elements(By.ID, 'aacb-captcha-header')
		has_arkose_iframe = self.driver.find_elements(By.ID, 'cvf-aamation-challenge-iframe')

		# ❗ CHỈ skip khi KHÔNG có cả 2
		if not has_normal_captcha and not has_arkose_iframe:
			return {
				'status': 'skipped',
				'message': 'No captcha present'
			}

		# =========================
		# 3️⃣ Chờ captcha thường biến mất
		# =========================
		print("[CAPTCHA] Waiting for normal captcha to be solved...")

		for i in range(3):
			try:
				self.wait.until(
					EC.invisibility_of_element_located(
						(By.ID, 'aacb-captcha-header')
					)
				)
				return {
					'status': 'success',
					'message': 'Captcha solved'
				}
			except TimeoutException:
				if i == 2:
					return {
						'status': 'error',
						'message': 'Captcha still present after 3 attempts'
					}
				time.sleep(random.uniform(8, 12))
			except Exception as e:
				return {
					'status': 'error',
					'message': f'Captcha solving error: {e}'
				}


	def get_code_mail(self, email, refresh_token, client_id):
		try:
			url = "https://tools.dongvanfb.net/api/get_code_oauth2"
			payload = {
				"email": email,
				"refresh_token": refresh_token,
				"client_id": client_id,
				"type": "amazon"
			}
			response = requests.post(url, json=payload, timeout=15)
			if response.status_code != 200:
				return {'status': 'error','message': f'HTTP {response.status_code}'}
			try:
				data = response.json()
			except Exception:
				return {'status': 'error','message': 'Invalid JSON response'}
			code = data.get('code', '')
			return {'status': 'success','message': code}
		except requests.exceptions.Timeout:
			return {'status': 'error','message': 'Request timeout'}
		except Exception as e:
			return {'status': 'error','message': f'get_code_mail error: {e}'}
	
	def verify_email_address(self, email, refresh_token, client_id, thread_name):
		try:
			self.wait.until(EC.visibility_of_element_located((By.XPATH, '//h1[normalize-space()="Verify email address"]')))
		except TimeoutException:
			return {'status': 'error','message': 'Verify email address not found'}
		checked = 0
		max_checked = 6
		code = ""
		while checked < max_checked:
			time.sleep(10)
			result = self.get_code_mail(email=email, refresh_token=refresh_token, client_id=client_id)
			if result['status'] != 'success':
				logger.error(f"{thread_name} {result['message']}")
				return {'status': 'error', 'message': result['message']}
			code = result.get('message', "").strip()
			if code:
				break
			try:
				resend_btn = self.wait.until(EC.element_to_be_clickable((By.ID, 'cvf-resend-link')))
				resend_btn.click()
			except TimeoutException:
				return {'status': 'error', 'message': 'Resend button not found'}
			checked += 1
		if not code:
			return {'status': 'error', 'message': 'OTP not received after max retries'}
		try:
			input_code = self.wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="cvf-input-code"]')))
			input_code.clear()
			input_code.send_keys(code)
		except TimeoutException:
			return {'status': 'error', 'message': 'Input code not found'}
		except Exception as e:
			return {'status': 'error', 'message': f'Input code error: {e}'}
		time.sleep(random.randint(1,3))
		try:
			button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Verify OTP Button"]')))
			button.click()
		except TimeoutException:
			return {'status': 'error', 'message': 'Verify OTP button not found'}
		except Exception as e:
			return {'status': 'error', 'message': f'Verify OTP button error: {e}'}
		return {'status': 'success','message': 'Verify OTP success'}
	def add_mobile_number(self, thread_name, phone_for_input, original_phone=None):
		"""
		Add and verify mobile number using HeroSMSPhoneManager.
		
		Args:
			thread_name: Thread identifier for logging
			phone_for_input: Phone number to input into Amazon form (may be cleaned)
			original_phone: Original phone number from HeroSMS (for SMS retrieval)
		
		Returns:
			dict: {'status': 'success'|'error'|'skipped', 'message': str}
		"""
		# Use original_phone for SMS retrieval, fallback to phone_for_input if not provided
		if original_phone is None:
			original_phone = phone_for_input
		
		# Check if phone manager is available
		if not self.phone_manager:
			logger.warning(f"{thread_name} No phone manager provided, skipping phone verification")
			return {'status': 'skipped', 'message': 'No phone manager available'}
		
		# DEBUG: Print current URL
		current_url = self.driver.current_url
		logger.warning(f"{thread_name} Current URL: {current_url}")
		
		# 1. Check if on "Add mobile number" page  
		try:
			# Amazon uses h2 tag, not h1
			header = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[self::h1 or self::h2][contains(normalize-space(), "Add mobile number")]')))
			logger.warning(f"{thread_name} Found 'Add mobile number' header")
		except TimeoutException:
			logger.warning(f"{thread_name} Add mobile number header not found, checking page source...")
			# DEBUG: Check what's on the page
			page_source = self.driver.page_source
			if "phone" in page_source.lower():
				logger.warning(f"{thread_name} Page contains 'phone' keyword")
			if "mobile" in page_source.lower():
				logger.warning(f"{thread_name} Page contains 'mobile' keyword")
			return {'status': 'skipped', 'message': 'Add mobile number page not found'}
		except Exception as e:
			return {'status': 'error', 'message': f'Page detection error: {e}'}
		
		# 2. Check phone parameter
		if not original_phone:
			return {'status': 'error', 'message': 'No phone available'}
		
		logger.warning(f"{thread_name} Attempting to input phone: {phone_for_input}")
		try:
			select_cc = Select(self.wait.until(EC.presence_of_element_located((By.ID, "cvf_phone_cc_native"))))
			select_cc.select_by_value("BR")
			time.sleep(0.5)
			brazil = self.wait.until(EC.element_to_be_clickable((By.XPATH,'//a[.//span[normalize-space()="Brazil"] and .//span[contains(text(), "+55")]]')))
			brazil.click()
			time.sleep(0.5)
		except TimeoutException:
			return {'status': 'error', 'message': 'Select Phone Code Timeout'}
		except Exception as e:
			return {'status': 'error', 'message': f'Select Phone Code Error: {e}'}
		try:
			# 3. Input phone number - Try multiple selectors
			input_phone = None
			selectors = [
				('ID', 'cvfPhoneNumber'),
				('ID', 'ap_customer_phone_number'),
				('NAME', 'cvfPhoneNumber'),
				('XPATH', '//input[@type="tel"]'),
				('XPATH', '//input[contains(@id, "phone") or contains(@id, "Phone")]'),
			]
			
			for selector_type, selector_value in selectors:
				try:
					if selector_type == 'ID':
						input_phone = self.wait.until(EC.presence_of_element_located((By.ID, selector_value)))
					elif selector_type == 'NAME':
						input_phone = self.wait.until(EC.presence_of_element_located((By.NAME, selector_value)))
					elif selector_type == 'XPATH':
						input_phone = self.wait.until(EC.presence_of_element_located((By.XPATH, selector_value)))
					
					if input_phone:
						break
				except TimeoutException:
					continue
			
			if not input_phone:
				return {'status': 'error', 'message': 'Phone input field not found with any selector'}
			
			input_phone.clear()
			# Clean phone number (remove +, -, spaces)
			clean_phone = phone_for_input.replace('+', '').replace('-', '').replace(' ', '')
			input_phone.send_keys(clean_phone)
			logger.warning(f"{thread_name} Entered phone: {clean_phone}")
			
			time.sleep(random.randint(1, 3))
			
			# 4. Click Continue/Send OTP button
			button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="cvf_action"]')))
			button.click()
			
			time.sleep(random.randint(2, 4))
			
			# 5. Wait for OTP input field
			otp_input = self.wait.until(EC.presence_of_element_located((By.ID, 'cvf-input-code')))
			
			# 6. Get SMS code from HeroSMS (wait up to 5 minutes)
			logger.warning(f"{thread_name} Waiting for SMS code (original phone: {original_phone})...")
			code = self.phone_manager.get_sms_code(original_phone, max_retries=30, retry_interval=10)
			if not code:
				logger.error(f"{thread_name} Failed to get SMS code")
				return {'status': 'error', 'message': 'SMS code not received'}
			logger.warning(f"{thread_name} Received SMS code: {code}")
			
			# 7. Input OTP code
			otp_input.clear()
			otp_input.send_keys(code)
			logger.warning(f"{thread_name} Entered OTP code")
			
			time.sleep(random.randint(1, 3))
			
			# 8. Submit OTP
			submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '(//input[@name="cvf_action" and @type="submit"])[1]')))
			submit_button.click()
			logger.warning(f"{thread_name} Submitted OTP")
			
			time.sleep(random.randint(2, 4))
			# 9. Success
			logger.warning(f"{thread_name} Phone verification successful")
			return {'status': 'success', 'message': 'Mobile number verified'}
			
		except Exception as e:
			# Release phone on any unexpected error
			logger.error(f"{thread_name} Unexpected error: {e}")
			return {'status': 'error', 'message': f'Unexpected error: {e}'}
	
	def main_flow(self, thread_name):
		phone = None
		phone_success = False
		faker = Faker("en_US")
		full_name = faker.name()
		password = faker.password(length=12)
		try:
			result = self.continue_captcha()
			if result['status'] != 'success' and result['status'] != 'skipped':
				logger.error(f"{thread_name} {result['message']}")
				return {'status': 'error','message': result['message']}
			self.driver.get("https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_ya_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")
			toolhelper = ToolHelper()
			outlook_full_data = toolhelper.read_email()
			if not outlook_full_data:
				return {'status': 'error', 'message': 'No email available'}
			email = outlook_full_data['email']
			password = outlook_full_data['password']
			refresh_token = outlook_full_data['refresh_token']
			client_id = outlook_full_data['client_id']
			result = self.create_account(email=email, full_name=full_name, password=password)
			if result['status'] != 'success':
				logger.error(f"{thread_name} {result['message']}")
				return {'status': 'error','message': result['message']}
			result = self.captcha_solving()
			if result['status'] == 'blocked':
				logger.warning(f"{thread_name} {result['message']}")
				return {'status': 'blocked','message': result['message']}
			if result['status'] != 'success' and result['status'] != 'skipped':
				logger.error(f"{thread_name} {result['message']}")
				return {'status': 'error','message': result['message']}
			result = self.verify_email_address(email=email, refresh_token=refresh_token, client_id=client_id, thread_name=thread_name)
			if result['status'] != 'success':
				logger.error(f"{thread_name} {result['message']}")
				return {'status': 'error','message': result['message']}
			# 🔒 ACQUIRE PHONE (LOCK BẮT ĐẦU TỪ ĐÂY)
			logger.warning(f"{thread_name} Acquiring phone from HeroSMS...")
			phone = self.phone_manager.acquire_phone()
			logger.warning(f"{thread_name} Phone acquired: {phone}")
			if not phone:
				return {'status': 'error', 'message': 'No phone available'}
			# Save original phone for HeroSMS API calls
			original_phone = phone
			# Clean phone for Amazon input (remove country code if needed)
			if phone.startswith("55"):
				phone_for_input = phone[2:]  # Remove Brazil prefix for input
			else:
				phone_for_input = phone
			result = self.add_mobile_number(thread_name, phone_for_input, original_phone)
			if result['status'] == 'success':
				phone_success = True
			elif result['status'] == 'skipped':
				phone_success = False
			else:
				phone_success = False
				return result
			current_url = self.driver.current_url
			if "new_account=1" not in current_url:
				return {'status': 'error', 'message': 'Account creation failed'}
			logger.warning(f"{thread_name} Account created successfully")
			return {'status': 'success', 'message': 'Account created successfully'}
		finally:
			if phone:
				self.phone_manager.release_phone(phone, success=phone_success)