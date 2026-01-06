import threading, time, os
from hidemium import Hidemium
from logger import Logger
from ctypes import c_bool
from multiprocessing import Value
from toolhelper import ToolHelper
from selenium import webdriver

logger = Logger()

def worker_thread(thread_id, stop_flag, position):
    thread_name = f"Thread-{thread_id}"
    try:
        while not stop_flag.value:
            hidemium = Hidemium()
            uuid = hidemium.create_profile_by_default(33296)
            remote_port, execute_path = hidemium.open_profile(uuid, proxy="HTTP|103.15.95.127|8013|qvinhWuIjK|qnLHiHDM")
            options = webdriver.ChromeOptions()
            options.binary_location = execute_path
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
            driver = webdriver.Chrome(options=options)
            driver.get('https://www.amazon.com/')
            time.sleep(60)
            driver.quit()
    except KeyboardInterrupt:
        logger.error(f"⛔ {thread_name} stopped.")

def main():
    logger.warning('AMAZON CREATOR WITH HIDEMIUM VER 1.0')
    logger.success('--------------------------------------------------')
    threads = int(logger.input_green("Nhập số luồng muốn chạy: "))
    logger.success('--------------------------------------------------')
    toolhelper = ToolHelper()
    positions = toolhelper.generator_positions(threads)
    stop_flag = Value(c_bool, False)
    thread_list = []
    for i in range(threads):
        t = threading.Thread(
            target=worker_thread,
            args=(i + 1, stop_flag, positions[i]),
            daemon=True
        )
        t.start()
        thread_list.append(t)
    try:
        logger.success("✅ All threads running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.error("⛔ Ctrl+C received. Stopping threads...")
        stop_flag.value = True

        # Wait for all threads to finish (max 5 seconds each)
        for t in thread_list:
            t.join(timeout=5)
        logger.success("✅ All threads stopped cleanly.")

if __name__ == "__main__":
    main()
