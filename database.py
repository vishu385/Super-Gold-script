import json
import os
import logging
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "database.json"
db_lock = Lock()

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)

def get_db():
    with db_lock:
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

def save_db(data):
    with db_lock:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)

def init_user(chat_id):
    chat_id = str(chat_id)
    db = get_db()
    if chat_id not in db:
        db[chat_id] = {
            "numbers": {}, # {"+91...": {"sent": 0}}
            "proxies": [],
            "config": {
                "limit": 10,
                "wait_time": 5,
                "loop": 1,
                "use_proxy": True,
                "is_attacking": False
            }
        }
        save_db(db)
    return db[chat_id]

def update_user(chat_id, user_data):
    chat_id = str(chat_id)
    db = get_db()
    db[chat_id] = user_data
    save_db(db)
