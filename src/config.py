import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    
    # LLM Settings
    LLM_API_KEY = os.getenv("LLM_API_KEY", DASHSCOPE_API_KEY)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen-plus")
    
    # Temp file settings
    TEMP_DIR = os.path.join(os.getcwd(), "temp")
    
    # App Settings
    SETTINGS_FILE = os.path.join(os.getcwd(), "settings.json")
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
        # 默认存在 main.py 同级的 saves 目录下
        default_save_dir = os.path.join(os.getcwd(), "saves")
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