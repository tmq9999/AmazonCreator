import requests

def get_code_mail(email, refresh_token, client_id):
	try:
		url = "https://tools.dongvanfb.net/api/get_code_oauth2"
		payload = {
			"email": email,
			"refresh_token": refresh_token,
			"client_id": client_id,
            "type": "amazon"
		}
		response = requests.post(url, json=payload)
		data = response.json()
		return data['code']
	except Exception as e:
		print(e)


res = get_code_mail("joshuaheath2620@outlook.com", "M.C546_BL2.0.U.-CmIHk*0JZCgDzxUDzJUhV!tNEKyGnHaqB8QtdsK4*L16SrdGqhYI8VlCv3bf4tz4ZAbXgZC8vkk04f7!GlfrJn4BCSSYUQErePgx64FGXJrESqKU4iN8fWg2gMwQXUXoXOztt5bJBW0CspDQnyStZvghLDUdXw!utADm32Xohkz4KVOQ!E4W73E2oX0pIuyU8AR*FFGSQBGcCecVDtRHNixQH9ZZuv8w9ICPtzz*Oj1Wh44UmVte2Jq!xSHTn9cTahQzH*qdC2wAV2WwflB7vJPVLro8KcDKOeGvk!nfGv4s8zohQOcYk6qZx3JAmwLdPbKKWcIhLYiv5OsrJs1hDOLuVkIhlNwEkjqVLXR9xXH*DgZGSXygQNKP2lYfEzpFBkV85Fq09GrC0Xbss9L1HdI$", "9e5f94bc-e8a4-4e73-b8be-63364c29d753")

print(res)