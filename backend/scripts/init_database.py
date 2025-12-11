"""
数据库初始化脚本
用于创建 SQLite 数据库和表结构
"""
import sqlite3
import sys
from pathlib import Path

# 添加 backend 目录到路径（脚本在 backend/scripts/ 下）
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings


def create_database():
    """创建数据库和表结构"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    # 确保数据库目录存在
    settings.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    
    db_path = settings.db_path
    logger.info(f"正在初始化数据库: {db_path}")
    
    # 如果数据库已存在，询问是否覆盖
    if Path(db_path).exists():
        response = input(f"数据库文件已存在: {db_path}\n是否要重新创建？这将删除所有现有数据！(y/N): ")
        if response.lower() != 'y':
            logger.info("取消初始化")
            return False
        Path(db_path).unlink()
        logger.info("已删除现有数据库文件")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建人员信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personnel_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                face_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                id_number TEXT UNIQUE,
                phone TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
                photo_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_id ON personnel_info(face_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON personnel_info(name)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ 数据库初始化成功！")
        logger.info(f"数据库位置: {db_path}")
        logger.info("表结构已创建，可以开始添加人员记录了。")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)

