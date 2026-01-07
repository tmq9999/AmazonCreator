import requests
from typing import Optional, Dict, List, Union


class HeroSMS:
	"""
	HeroSMS API Client - Compatible with SMS-Activate protocol
	
	Official API Documentation: https://hero-sms.com
	
	Features:
	- Get phone numbers for SMS verification
	- Check activation status and retrieve SMS codes
	- Manage activations (cancel, set status)
	- Get balance, prices, countries, services
	
	Thread Safety:
	- Each instance is NOT thread-safe (use one instance per thread)
	- Or use locks when sharing across threads
	"""
	
	def __init__(self, api_key: str, base_url: str = "https://hero-sms.com/stubs/handler_api.php"):
		"""
		Initialize HeroSMS client
		
		Args:
			api_key: Your HeroSMS API key
			base_url: API base URL (default: https://hero-sms.com/stubs/handler_api.php)
		"""
		self.api_key = api_key
		self.base_url = base_url
	
	def _request(self, action: str, params: Optional[Dict] = None) -> Union[str, Dict]:
		"""
		Internal method to make API requests
		
		Args:
			action: API action name
			params: Additional query parameters
		
		Returns:
			Response text or parsed JSON
		
		Raises:
			requests.RequestException: On network errors
		"""
		query_params = {
			'action': action,
			'api_key': self.api_key
		}
		
		if params:
			query_params.update(params)
		
		response = requests.get(self.base_url, params=query_params, timeout=30)
		response.raise_for_status()
		
		# Try to parse as JSON, otherwise return text
		try:
			return response.json()
		except:
			return response.text
	
	# ==================== BALANCE ====================
	
	def get_balance(self) -> Dict[str, Union[str, float]]:
		"""
		Get account balance
		
		Returns:
			dict: {'status': 'success'|'error', 'balance': float, 'raw': str}
			
		Example:
			>>> client.get_balance()
			{'status': 'success', 'balance': 123.45, 'raw': 'ACCESS_BALANCE:123.45'}
		"""
		result = self._request('getBalance')
		
		if isinstance(result, str):
			if result.startswith('ACCESS_BALANCE:'):
				balance = float(result.split(':')[1])
				return {'status': 'success', 'balance': balance, 'raw': result}
			else:
				return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected response format', 'raw': str(result)}
	
	# ==================== NUMBER ACTIVATION ====================
	
	def get_number(self, service: str, country: int, operator: Optional[str] = None, 
	               max_price: Optional[float] = None, ref: Optional[str] = None) -> Dict:
		"""
		Request a phone number for activation
		
		Args:
			service: Service code (e.g., 'ig' for Instagram, 'wa' for WhatsApp, 'am' for Amazon)
			country: Country code (numeric)
			operator: Optional operator name
			max_price: Optional maximum price
			ref: Optional referral code
		
		Returns:
			dict: {'status': 'success'|'error', 'activation_id': str, 'phone': str, ...}
		
		Example:
			>>> client.get_number('am', 6)  # Amazon, USA
			{'status': 'success', 'activation_id': '123456', 'phone': '1234567890'}
		"""
		params = {
			'service': service,
			'country': country
		}
		
		if operator:
			params['operator'] = operator
		if max_price is not None:
			params['maxPrice'] = max_price
		if ref:
			params['ref'] = ref
		
		result = self._request('getNumber', params)
		
		if isinstance(result, str):
			if result.startswith('ACCESS_NUMBER:'):
				parts = result.split(':')
				return {
					'status': 'success',
					'activation_id': parts[1],
					'phone': parts[2],
					'raw': result
				}
			else:
				return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_number_v2(self, service: str, country: int, operator: Optional[str] = None,
	                  max_price: Optional[float] = None, ref: Optional[str] = None) -> Dict:
		"""
		Request a phone number (V2 - returns more details)
		
		Args:
			service: Service code
			country: Country code
			operator: Optional operator
			max_price: Optional max price
			ref: Optional referral code
		
		Returns:
			dict: Detailed activation info including cost, currency, operator, etc.
		
		Example:
			>>> client.get_number_v2('am', 6)
			{
				'status': 'success',
				'activationId': 635468024,
				'phoneNumber': '79584******',
				'activationCost': 12.5,
				...
			}
		"""
		params = {
			'service': service,
			'country': country
		}
		
		if operator:
			params['operator'] = operator
		if max_price is not None:
			params['maxPrice'] = max_price
		if ref:
			params['ref'] = ref
		
		result = self._request('getNumberV2', params)
		
		if isinstance(result, dict):
			result['status'] = 'success'
			return result
		elif isinstance(result, str):
			return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	# ==================== STATUS MANAGEMENT ====================
	
	def set_status(self, activation_id: str, status: int) -> Dict:
		"""
		Set activation status
		
		Args:
			activation_id: Activation ID from get_number()
			status: Status code:
			        1 = Ready (number received, waiting for code)
			        3 = Request another SMS
			        6 = Complete activation
			        8 = Cancel activation
		
		Returns:
			dict: {'status': 'success'|'error', 'message': str, ...}
		
		Example:
			>>> client.set_status('123456', 1)  # Mark as ready
			>>> client.set_status('123456', 6)  # Complete
			>>> client.set_status('123456', 8)  # Cancel
		"""
		params = {
			'id': activation_id,
			'status': status
		}
		
		result = self._request('setStatus', params)
		
		if isinstance(result, str):
			if result.startswith('ACCESS_'):
				return {'status': 'success', 'message': result, 'raw': result}
			else:
				return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_status(self, activation_id: str) -> Dict:
		"""
		Get activation status and SMS code
		
		Args:
			activation_id: Activation ID
		
		Returns:
			dict: {'status': 'success'|'wait'|'error', 'code': str|None, ...}
		
		Status values:
			STATUS_WAIT_CODE - Waiting for SMS
			STATUS_WAIT_RETRY - Waiting for code clarification
			STATUS_OK:code - Code received
			STATUS_CANCEL - Activation canceled
		
		Example:
			>>> client.get_status('123456')
			{'status': 'success', 'code': '123456', 'raw': 'STATUS_OK:123456'}
		"""
		params = {'id': activation_id}
		result = self._request('getStatus', params)
		
		if isinstance(result, str):
			if result.startswith('STATUS_OK:'):
				code = result.split(':')[1] if ':' in result else None
				return {'status': 'success', 'code': code, 'raw': result}
			elif result == 'STATUS_WAIT_CODE':
				return {'status': 'wait', 'code': None, 'message': 'Waiting for SMS', 'raw': result}
			elif result.startswith('STATUS_WAIT_RETRY:'):
				return {'status': 'wait', 'code': None, 'message': 'Waiting for retry', 'raw': result}
			elif result == 'STATUS_CANCEL':
				return {'status': 'canceled', 'code': None, 'raw': result}
			else:
				return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_status_v2(self, activation_id: str) -> Dict:
		"""
		Get detailed activation status (V2)
		
		Returns more information including SMS text, call info, etc.
		
		Args:
			activation_id: Activation ID
		
		Returns:
			dict: Detailed status including verificationType, sms, call info
		"""
		params = {'id': activation_id}
		result = self._request('getStatusV2', params)
		
		if isinstance(result, dict):
			result['status'] = 'success'
			return result
		elif isinstance(result, str):
			return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	# ==================== ACTIVATIONS ====================
	
	def get_active_activations(self) -> Dict:
		"""
		Get list of all active activations
		
		Returns:
			dict: {'status': 'success'|'error', 'activations': List[Dict], ...}
		
		Example:
			>>> client.get_active_activations()
			{
				'status': 'success',
				'activeActivations': [
					{
						'activationId': '635468021',
						'serviceCode': 'vk',
						'phoneNumber': '79********1',
						'smsCode': '[CODE]',
						...
					}
				]
			}
		"""
		result = self._request('getActiveActivations')
		
		if isinstance(result, dict):
			if result.get('status') == 'error':
				return result
			result['status'] = 'success'
			return result
		elif isinstance(result, str):
			return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_history(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
		"""
		Get activation history
		
		Args:
			start_date: Optional start date (format: YYYY-MM-DD)
			end_date: Optional end date (format: YYYY-MM-DD)
		
		Returns:
			dict: {'status': 'success'|'error', 'history': List[Dict], ...}
		"""
		params = {}
		if start_date:
			params['start'] = start_date
		if end_date:
			params['end'] = end_date
		
		result = self._request('getHistory', params)
		
		if isinstance(result, list):
			return {'status': 'success', 'history': result}
		elif isinstance(result, str):
			return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	# ==================== INFORMATION ====================
	
	def get_countries(self) -> Dict:
		"""
		Get list of available countries
		
		Returns:
			dict: {'status': 'success', 'countries': List[Dict]}
		
		Example:
			>>> client.get_countries()
			{
				'status': 'success',
				'countries': [
					{'id': 2, 'rus': '...', 'eng': 'Kazakhstan', 'visible': 1, ...}
				]
			}
		"""
		result = self._request('getCountries')
		
		if isinstance(result, list):
			return {'status': 'success', 'countries': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_services(self) -> Dict:
		"""
		Get list of available services
		
		Returns:
			dict: {'status': 'success', 'services': List[Dict]}
		
		Example:
			>>> client.get_services()
			{
				'status': 'success',
				'services': [
					{'code': 'aoo', 'name': 'Pegasus Airlines'},
					...
				]
			}
		"""
		result = self._request('getServicesList')
		
		if isinstance(result, dict):
			return result
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_operators(self, country: int) -> Dict:
		"""
		Get list of operators for a country
		
		Args:
			country: Country code
		
		Returns:
			dict: {'status': 'success', 'countryOperators': {...}}
		
		Example:
			>>> client.get_operators(6)  # USA
			{
				'status': 'success',
				'countryOperators': {
					'6': ['verizon', 'att', 't-mobile', ...]
				}
			}
		"""
		params = {'country': country}
		result = self._request('getOperators', params)
		
		if isinstance(result, dict):
			return result
		elif isinstance(result, str):
			return {'status': 'error', 'message': result, 'raw': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_prices(self, service: Optional[str] = None, country: Optional[int] = None) -> Dict:
		"""
		Get current prices
		
		Args:
			service: Optional service code to filter
			country: Optional country code to filter
		
		Returns:
			dict: {'status': 'success', 'prices': [...]}
		
		Example:
			>>> client.get_prices('am', 6)  # Amazon prices for USA
		"""
		params = {}
		if service:
			params['service'] = service
		if country is not None:
			params['country'] = country
		
		result = self._request('getPrices', params)
		
		if isinstance(result, (list, dict)):
			return {'status': 'success', 'prices': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}
	
	def get_top_countries_by_service(self, service: Optional[str] = None) -> Dict:
		"""
		Get top countries by service availability
		
		Args:
			service: Optional service code
		
		Returns:
			dict: Top countries with availability and pricing info
		"""
		params = {}
		if service:
			params['service'] = service
		
		result = self._request('getTopCountriesByService', params)
		
		if isinstance(result, list):
			return {'status': 'success', 'countries': result}
		
		return {'status': 'error', 'message': 'Unexpected format', 'raw': str(result)}


# ==================== USAGE EXAMPLES ====================

if __name__ == "__main__":
	# Example usage
	api_key = "YOUR_API_KEY_HERE"
	client = HeroSMS(api_key)
	
	# 1. Check balance
	balance = client.get_balance()
	print(f"Balance: {balance}")
	
	# 2. Get a phone number for Amazon in USA
	number_result = client.get_number_v2(service='am', country=6)
	if number_result['status'] == 'success':
		activation_id = number_result['activationId']
		phone = number_result['phoneNumber']
		print(f"Got phone: {phone}, activation ID: {activation_id}")
		
		# 3. Mark as ready (waiting for SMS)
		client.set_status(activation_id, 1)
		
		# 4. Check for SMS code
		import time
		for i in range(30):  # Try for 5 minutes
			status = client.get_status(activation_id)
			if status['status'] == 'success' and status['code']:
				print(f"Got code: {status['code']}")
				# 5. Complete activation
				client.set_status(activation_id, 6)
				break
			elif status['status'] == 'wait':
				print("Waiting for SMS...")
				time.sleep(10)
			else:
				print(f"Error: {status}")
				break
	else:
		print(f"Error getting number: {number_result}")
