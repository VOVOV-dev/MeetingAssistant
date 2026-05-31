import os
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
    
    @classmethod
    def ensure_temp_dir(cls):
        if not os.path.exists(cls.TEMP_DIR):
            os.makedirs(cls.TEMP_DIR)
