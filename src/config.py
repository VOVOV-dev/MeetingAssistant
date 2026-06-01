import os
import json
import sys
from dotenv import load_dotenv
from datetime import datetime

def get_app_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


BASE_DIR = get_app_base_dir()
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)

class Config:
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

    @staticmethod
    def _base_dir() -> str:
        return BASE_DIR

    @staticmethod
    def _env_file() -> str:
        return ENV_FILE
    
    # LLM Settings
    LLM_API_KEY = os.getenv("LLM_API_KEY", DASHSCOPE_API_KEY)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen-plus")
    
    # Temp file settings
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    
    # App Settings
    SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
    _settings = {}
    
    @classmethod
    def load_settings(cls):
        if os.path.exists(cls.SETTINGS_FILE):
            try:
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    cls._settings = json.load(f)
            except:
                cls._settings = {}
        else:
            cls._settings = {}
            
    @classmethod
    def save_settings(cls):
        with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cls._settings, f, indent=4, ensure_ascii=False)
            
    @classmethod
    def get_save_dir(cls) -> str:
        cls.load_settings()
        # 默认存在程序主目录下的 saves 目录中
        default_save_dir = os.path.join(cls._base_dir(), "saves")
        save_dir = cls._settings.get("save_dir", default_save_dir)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        return save_dir
        
    @classmethod
    def set_save_dir(cls, new_dir: str):
        cls._settings["save_dir"] = new_dir
        cls.save_settings()

    @classmethod
    def ensure_temp_dir(cls):
        if not os.path.exists(cls.TEMP_DIR):
            os.makedirs(cls.TEMP_DIR)

# 初始化加载配置
Config.load_settings()

def log(msg: str):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        path = os.path.join(BASE_DIR, 'app.log')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass