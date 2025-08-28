import threading
import queue
import time
from module import utils

# Queue để quản lý các thông báo TTS
tts_queue = queue.Queue()
tts_worker_running = False

def start_tts_worker():
    """
    Khởi động worker thread để xử lý TTS bất đồng bộ
    """
    global tts_worker_running
    if not tts_worker_running:
        tts_worker_running = True
        threading.Thread(target=tts_worker, daemon=True).start()

def tts_worker():
    """
    Worker thread xử lý queue TTS
    """
    global tts_worker_running
    while tts_worker_running:
        try:
            # Lấy message từ queue với timeout
            message = tts_queue.get(timeout=1)
            if message is None:  # Signal để dừng worker
                break
            # Thực hiện TTS
            utils.speak_vie(message)
            tts_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"TTS Error: {e}")

def speak_async(message):
    """
    Thêm thông báo vào queue để phát bất đồng bộ
    
    Args:
        message (str): Nội dung cần đọc
    """
    if not tts_worker_running:
        start_tts_worker()
    
    # Clear queue cũ nếu có (chỉ giữ thông báo mới nhất)
    while not tts_queue.empty():
        try:
            tts_queue.get_nowait()
        except queue.Empty:
            break
    
    # Thêm thông báo mới
    tts_queue.put(message)

def stop_tts_worker():
    """
    Dừng TTS worker thread
    """
    global tts_worker_running
    tts_worker_running = False
    tts_queue.put(None)  # Signal để dừng