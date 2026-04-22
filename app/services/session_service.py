from collections import deque
import threading

class SessionManager:
    def __init__(self, history_limit: int = 10):
        self.history_limit = history_limit
        self.sessions = {}
        self.lock = threading.Lock()

    def get_history(self, sender_id: str) -> list:
        with self.lock:
            if sender_id not in self.sessions:
                return []
            return list(self.sessions[sender_id])

    def add_message(self, sender_id: str, role: str, content: str):
        with self.lock:
            if sender_id not in self.sessions:
                self.sessions[sender_id] = deque(maxlen=self.history_limit)
            
            self.sessions[sender_id].append({
                "role": role,
                "content": content
            })

session_manager = SessionManager()
