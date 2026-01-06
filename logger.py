from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

class Logger:
	def __init__(self):
		pass
	
	def _get_timestamp(self):
		return datetime.now().strftime("%H:%M:%S")
	
	def warning(self, message):
		timestamp = self._get_timestamp()
		print(f"{Fore.YELLOW}{timestamp} - {message}{Style.RESET_ALL}")
	
	def error(self, message):
		timestamp = self._get_timestamp()
		print(f"{Fore.RED}{timestamp} - {message}{Style.RESET_ALL}")
	
	def success(self, message):
		timestamp = self._get_timestamp()
		print(f"{Fore.GREEN}{timestamp} - {message}{Style.RESET_ALL}")
	
	def input_green(self, text):
		return input(f"{Fore.GREEN}{text}{Style.RESET_ALL}")
	
	def input_yellow(self, text):
		return input(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")
	
	def input_red(self, text):
		return input(f"{Fore.RED}{text}{Style.RESET_ALL}")