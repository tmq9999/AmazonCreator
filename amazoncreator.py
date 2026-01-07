import time, random, requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from logger import Logger
from toolhelper import ToolHelper
from faker import Faker
logger = Logger()

class AmazonCreator:
	
	def __init__(self, driver, wait):
		self.driver = driver
		self.wait = wait

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

	def create_account(self, email):
		faker = Faker("en_US")
		full_name = faker.name()
		password = faker.password(length=12)
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
		print(f"Email: {email}, Password: {password}")
		return {'status': 'success','message': f'create_account success'}

	def captcha_solving(self):
    # --- 1️⃣ Detect Arkose Labs (iframe captcha nặng) ---
		try:
			self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'cvf-aamation-challenge-iframe')))
			if self.driver.find_elements(By.ID, 'aacb-arkose-elements'):
				return {'status': 'blocked','message': 'Arkose Labs challenge detected'}
		except TimeoutException:
			pass
		except Exception as e:
			return {'status': 'error','message': f'Arkose detection error: {e}'}
		finally:
			try:
				self.driver.switch_to.default_content()
			except:
				pass

		# --- 2️⃣ Captcha thường ---
		if not self.driver.find_elements(By.ID, 'aacb-captcha-header'):
			return {'status': 'skipped','message': 'No captcha present'}
		print("thay captcha aws dang doi")
		for i in range(3):
			try:
				self.wait.until(EC.invisibility_of_element_located((By.ID, 'aacb-captcha-header')))
				return {'status': 'success','message': 'Captcha solved'}
			except TimeoutException:
				if i == 2:
					return {'status': 'error','message': 'Captcha still present after 3 attempts'}
				time.sleep(random.uniform(8, 12))
			except Exception as e:
				return {'status': 'error','message': f'Captcha solving error: {e}'}

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
			time.sleep(5)
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

	def add_mobile_number(self):
		try:
			input_email = self.wait.until(EC.presence_of_element_located((By.ID, 'ap_email_login')))
			input_email.clear()
			input_email.send_keys()
		except TimeoutException:
			return {'status': 'skipped', 'message': 'Add mobile number not found'}
		except Exception as e:
			return {'status': 'error', 'message': f'Add mobile number error: {e}'}
	
	def main_flow(self, thread_name):
		# result = self.continue_captcha()
		# if result['status'] != 'success' and result['status'] != 'skipped':
		# 	logger.error(f"{thread_name} {result['message']}")
		# 	return {'status': 'error','message': result['message']}
		# self.driver.get("https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_ya_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")
		# toolhelper = ToolHelper()
		# outlook_full_data = toolhelper.read_email()
		# email = outlook_full_data['email']
		# password = outlook_full_data['password']
		# refresh_token = outlook_full_data['refresh_token']
		# client_id = outlook_full_data['client_id']
		# result = self.create_account(email)
		# if result['status'] != 'success':
		# 	logger.error(f"{thread_name} {result['message']}")
		# 	return {'status': 'error','message': result['message']}
		# result = self.captcha_solving()
		# if result['status'] != 'success' and result['status'] != 'skipped':
		# 	logger.error(f"{thread_name} {result['message']}")
		# 	return {'status': 'error','message': result['message']}
		# result = self.verify_email_address(email=email, refresh_token=refresh_token, client_id=client_id, thread_name=thread_name)
		# if result['status'] != 'success':
		# 	logger.error(f"{thread_name} {result['message']}")
		# 	return {'status': 'error','message': result['message']}
		


