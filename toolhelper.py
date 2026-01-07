import os
import platform
import time

if platform.system() == "Windows":
	import msvcrt
else:
	import fcntl

class ToolHelper:
    
	def generator_positions(self, thread):
		POPUP_WIDTH = 400
		POPUP_HEIGHT = 300
		COLUMNS = 4
		MARGIN_X = 10
		MARGIN_Y = 10
		START_X = 0
		START_Y = 0
		positions = []
		for i in range(thread):
			row = i // COLUMNS
			col = i % COLUMNS
			x = START_X + col * (POPUP_WIDTH + MARGIN_X)
			y = START_Y + row * (POPUP_HEIGHT + MARGIN_Y)
			positions.append((x, y))
		return positions

	def read_email(self, file_path="mail.txt", max_retries=10, retry_delay=0.1):
		for attempt in range(max_retries):
			try:
				if not os.path.exists(file_path):
					return None
				
				size = os.path.getsize(file_path)
				if size == 0:
					return None
				
				with open(file_path, 'r+', encoding='utf-8') as f:
					if platform.system() == "Windows":
						msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, size)
					else:
						fcntl.flock(f.fileno(), fcntl.LOCK_EX)
					
					try:
						lines = f.readlines()
						
						if not lines:
							return None
						
						first_line = lines[0].strip()
						remaining_lines = lines[1:]
						
						f.seek(0)
						f.truncate()
						f.writelines(remaining_lines)
						
					finally:
						if platform.system() == "Windows":
							msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, size)
						else:
							fcntl.flock(f.fileno(), fcntl.LOCK_UN)
				
				if first_line:
					parts = first_line.split('|')
					if len(parts) != 4:
						with open("invalid_mail.txt", "a", encoding="utf-8") as log:
							log.write(first_line + "\n")
						print(f"[read_email] Invalid format, logged to invalid_mail.txt: {first_line}")
						return None
					
					return {
						'email': parts[0],
						'password': parts[1],
						'refresh_token': parts[2],
						'client_id': parts[3]
					}
				else:
					return None
					
			except Exception as e:
				if attempt < max_retries - 1:
					time.sleep(retry_delay)
				else:
					print(f"[read_email] failed after {max_retries} attempts: {e}")
					return None
		
		return None

	