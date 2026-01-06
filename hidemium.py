import requests, json

BASE_URL = "http://localhost:2222"

class Hidemium:
	def __init__(self):
		self.headers = {
			'Accept': 'application/json, text/plain, */*',
			'Accept-Language': 'en-US',
			'Connection': 'keep-alive',
			'Content-Type': 'application/json',
			'Cookie': '_ga=GA1.1.1045764629.1714978165; _ga_M8T88PC7LF=GS1.1.1715064563.4.1.1715065615.0.0.0',
			'Referer': 'http://localhost:6686/',
			'Sec-Fetch-Dest': 'empty',
			'Sec-Fetch-Mode': 'cors',
			'Sec-Fetch-Site': 'same-site',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Hidemium_4/4.0.7 Chrome/122.0.6261.156 Electron/29.3.2 Safari/537.36',
			'sec-ch-ua': '"Not(A:Brand";v="24", "Chromium";v="122"',
			'sec-ch-ua-mobile': '?0',
			'sec-ch-ua-platform': '"Windows"'
		}

	def open_profile(self, uuid, command=None, proxy=None):
		url = BASE_URL + f"/openProfile?uuid={uuid}"
		if command:
			url += f"&command={command}"
		if proxy:
			url += f"&proxy={proxy}"

		response = requests.get(url, headers=self.headers)
		result = response.json()

		if result.get("status") != "successfully":
			raise Exception(f"Open profile failed: {result}")

		data = result["data"]

		remote_port = data["remote_port"]
		execute_path = data["execute_path"]

		return remote_port, execute_path

	def close_profile(self, uuid):
		url = BASE_URL + f"/closeProfile?uuid={uuid}"
		payload = {}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def checking(self, uuid):
		url = BASE_URL + f"/authorize?uuid={uuid}"
		payload = {}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def list_browser(self):
		url = BASE_URL + "/v1/browser/list?is_local=false"
		payload = "{\r\n    \"orderName\": 0,      //sắp xếp theo name: 0 là ko sắp xếp, 1 là A-Z , 2 là Z-A\r\n    \"orderLastOpen\": 0,\r\n    \"page\": 1,     //chọn trang hiển thị\r\n    \"limit\": 10,   // Số profile hiển thị trong 1 trang\r\n    \"search\": \"\",  //Nhập tên profile cần tìm , có thể để trống\r\n    \"status\": \"\",      // id của status , có thể để trống\r\n    \"date_range\": [\r\n        \"\",\r\n        \"\"\r\n    ],   //Nhập khoảng ngày tạo profile theo định dạng yyyy-mm-dd\r\n   \r\n    \"folder_id\": []   //Nhập id của folder, có thể để trống\r\n    \r\n}"
		response = requests.request("POST", url, headers=self.headers, data=payload)
		return response.json()

	def list_default_config(self):
		url = BASE_URL + "/v2/default-config?page=1&limit=10"
		payload={}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def list_status(self):
		url = BASE_URL + "/v2/status-profile?is_local=true"
		payload={}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()
				
	def list_tag(self):
		url = BASE_URL + "/v2/tag?is_local=true"
		payload={}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def list_version(self):
		url = BASE_URL + "/v2/browser/get-list-version"
		payload={}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def get_browser_by_uuid(self, uuid):
		url = BASE_URL + f"/v2/browser/get-profile-by-uuid/{uuid}?is_local=false"
		payload={}
		files={}
		response = requests.request("GET", url, headers=self.headers, data=payload, files=files)
		return response.json()

	def get_list_folder(self):
		url = BASE_URL + "/v1/folder/list?is_local=false&page=1&limit=5"
		payload={}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def change_fingerprint(self, uuid):
		url = BASE_URL + "/v2/browser/change-fingerprint"
		payload = json.dumps({
			"profile_uuid": uuid
		})
		response = requests.request("PUT", url, headers=self.headers, data=payload)
		return response.json()

	def update_note(self, uuid, note):
		url = BASE_URL + "/v2/browser/update-note?is_local=false"
		payload = json.dumps({
			"note": note,
			"profile_uuid": uuid
		})
		response = requests.request("PUT", url, headers=self.headers, data=payload)
		return response.json()

	def update_name(self, uuid, name):
		url = BASE_URL + "/v2/browser/update-once?is_local=true"

		payload = json.dumps({
			"column": "name",
			"profile_uuid": uuid,
			"data": name
		})
		response = requests.request("PUT", url, headers=self.headers, data=payload)
		return response.json()

	def sync_tag(self, uuid, tags):
		url = BASE_URL + "/v2/tag?is_local=false"
		payload = json.dumps({
			"tags": tags,
			"profile_uuid": uuid
		})
		response = requests.request("POST", url, headers=self.headers, data=payload)
		return response.json()

	def change_status(self, uuid, id):
		url = BASE_URL + "/v2/status-profile/change-status"
		payload = json.dumps({
			"browser_uuid": uuid,
			"id": id #nhập id của status , default status: '0'- No Status, '-1'-Ban, '-2' - Ready, '-3'- New.
		})
		response = requests.request("PUT", url, headers=self.headers, data=payload)
		return response.json()

	def delete_profile(self, uuid):
		url = BASE_URL + "/v1/browser/destroy?is_local=false"
		payload = json.dumps({
			"uuid_browser": [
				uuid
			]
		})
		response = requests.request("DELETE", url, headers=self.headers, data=payload)
		return response.json()

	def edit_proxy(self, proxy_type, port, user, password, checker, check_before_start, ip, browser_uuid, details={}, status="NEW"):
		url = BASE_URL + "/v2/proxy/quick-edit?is_local=true"
		payload = json.dumps({
			"type": proxy_type,
			"port": port,
			"user": user,
			"pass": password,
			"checker": checker,
			"checkBeforeStart": check_before_start,
			"ip": ip,
			"browser_uuid": browser_uuid,
			"details": details,
			"status": status
		})
		response = requests.request("PUT", url, headers=self.headers, data=payload)
		return response.json()

	def update_profile_proxy(self, browser_update, is_local=False):
		url = BASE_URL + f"/v2/browser/proxy/update?is_local={str(is_local).lower()}"
		payload = json.dumps({
			"browser_update": browser_update
		})
		response = requests.request("POST", url, headers=self.headers, data=payload)
		return response.json()

	def list_script(self, page=1, limit=10):
		url = BASE_URL + f"/v2/automation/script?page={page}&limit={limit}"
		payload = {}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def create_profile_by_default(self, default_config_id, is_local=False):
		url = BASE_URL + f"/create-profile-by-default?is_local={str(is_local).lower()}"
		payload = json.dumps({
			"defaultConfigId": default_config_id
		})
		response = requests.request("POST", url, headers=self.headers, data=payload)
		data = response.json()
		if response.status_code != 200 or "content" not in data:
		    raise Exception(f"Create profile failed: {data}")
		return data["content"].get("uuid")

	def create_profile_custom(self, config, is_local=True):
		url = BASE_URL + f"/create-profile-custom?is_local={str(is_local).lower()}"
		payload = json.dumps(config)
		response = requests.request("POST", url, headers=self.headers, data=payload)
		return response.json()

	def build_profile_config(self, name, os="win", browser="chrome", version="143", language="en-US", resolution="1920x1080", proxy=None, folder_name=None, start_url="https://ipgeo.us/", canvas=True, webgl_image=False, audio_context=False, device_memory=8, hardware_concurrency=4, command=None, cookies=None, checkname=False, **kwargs):
		config = {
			"os": os,
			"browser": browser,
			"version": version,
			"name": name,
			"language": language,
			"resolution": resolution,
			"canvas": canvas,
			"webGLImage": webgl_image,
			"audioContext": audio_context,
			"webGLMetadata": False,
			"clientRectsEnable": False,
			"noiseFont": False,
			"deviceMemory": device_memory,
			"hardwareConcurrency": hardware_concurrency,
			"StartURL": start_url,
			"userAgent": "",
			"checkname": checkname
		}
		if proxy:
			config["proxy"] = proxy
		if folder_name:
			config["folder_name"] = folder_name
		if command:
			config["command"] = command
		if cookies:
			config["cookies"] = cookies
		config.update(kwargs)
		return config

	def get_user_token(self):
		url = BASE_URL + "/user-settings/token"
		payload = {}
		response = requests.request("GET", url, headers=self.headers, data=payload)
		return response.json()

	def add_profile_to_folder(self, folder_uuid, profile_uuids, is_local=True):
		url = BASE_URL + f"/v1/folder/{folder_uuid}/add-browser?is_local={str(is_local).lower()}"
		if isinstance(profile_uuids, str):
			profile_uuids = [profile_uuids]
		payload = json.dumps({
			"uuid_browser": profile_uuids
		})
		response = requests.request("POST", url, headers=self.headers, data=payload)
		return response.json()

	def remove_proxy_from_profile(self, browser_uuid, is_local=False):
		url = BASE_URL + f"/v2/proxy/quick-edit?is_local={str(is_local).lower()}"
		payload = json.dumps({
			"browser_uuid": browser_uuid,
			"id": -1
		})
		response = requests.request("PUT", url, headers=self.headers, data=payload)
		return response.json()
