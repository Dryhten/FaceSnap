"""
应用配置管理
使用.env文件进行配置管理
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 加载.env文件
# 优先级：.env.local > .env > 环境变量 > 默认值
# settings.py 在 backend/config/ 目录下，BASE_DIR 应该是项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
ENV_LOCAL_FILE = BASE_DIR / ".env.local"

# 先加载.env，再加载.env.local（.env.local优先级更高）
# 确保在导入 os.getenv 之前加载环境变量
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=False)
if ENV_LOCAL_FILE.exists():
    load_dotenv(ENV_LOCAL_FILE, override=True)


class Settings:
    """应用配置类"""
    
    # 基础路径配置
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "backend" / "data"
    DATABASE_DIR: Path = DATA_DIR / "database"  # SQLite 数据库文件目录
    FACES_DIR: Path = DATA_DIR / "faces"  # 人脸图片存储目录
    MODELS_DIR: Path = DATA_DIR / "models"  # 模型文件存储目录
    
    # 数据库配置（SQLite）
    DB_PATH: Path = DATABASE_DIR / "personnel.db"  # SQLite 数据库文件路径
    
    # 模型配置
    FACE_DETECTION_THRESHOLD: float = float(os.getenv("FACE_DETECTION_THRESHOLD", "0.9"))
    FACE_RECOGNITION_THRESHOLD: float = float(os.getenv("FACE_RECOGNITION_THRESHOLD", "0.7"))
    # 设备配置：优先使用环境变量，否则根据CUDA可用性自动选择
    _DEVICE_RAW: str = os.getenv(
        "DEVICE",
        "cuda:0" if os.getenv("CUDA_VISIBLE_DEVICES") is not None else "cpu"
    )
    
    @staticmethod
    def _normalize_device(device_str: str) -> str:
        """
        规范化设备名称，将 MUSA 设备转换为 PyTorch 可识别的设备类型
        
        MUSA GPU 使用 privateuseone 设备类型
        """
        if device_str.startswith("musa:"):
            # MUSA GPU 使用 privateuseone 设备类型
            device_id = device_str.split(":")[1] if ":" in device_str else "0"
            return f"privateuseone:{device_id}"
        return device_str
    
    @property
    def DEVICE(self) -> str:
        """获取规范化后的设备名称"""
        return self._normalize_device(self._DEVICE_RAW)
    
    # 服务配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB，默认10MB
    ALLOWED_IMAGE_EXTENSIONS: set = {
        ext.strip()
        for ext in os.getenv("ALLOWED_IMAGE_EXTENSIONS", ".jpg,.jpeg,.png,.bmp").split(",")
    }
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    def __init__(self):
        """初始化配置，确保目录存在"""
        # 确保必要的目录存在
        self.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self.FACES_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    @property
    def db_path(self) -> str:
        """获取数据库文件路径（字符串格式，用于 sqlite3）"""
        return str(self.DB_PATH)
    
    def __repr__(self) -> str:
        """配置信息字符串表示（隐藏敏感信息）"""
        return (
            f"Settings("
            f"DB_PATH={self.DB_PATH}, "
            f"API_HOST={self.API_HOST}, "
            f"API_PORT={self.API_PORT}, "
            f"DEVICE={self.DEVICE}"
            f")"
        )


# 创建全局配置实例
settings = Settings()

# 在模块加载时设置 TORCH_HOME，让 facenet-pytorch 将模型下载到项目目录
# 必须在导入 facenet-pytorch 之前设置，所以在这里设置
if 'TORCH_HOME' not in os.environ:
    os.environ['TORCH_HOME'] = str(settings.MODELS_DIR)

