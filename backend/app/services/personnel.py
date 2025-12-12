import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from app.core.config import settings


class PersonnelService:
    def __init__(self):
        self.db_path = settings.db_path

    def initialize_database(self):
        """初始化数据库，如果不存在或表结构不完整则创建"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personnel_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    face_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    id_number TEXT UNIQUE,
                    phone TEXT,
                    address TEXT,
                    gender TEXT CHECK(gender IN ('male', 'female', 'other', '')),
                    category TEXT,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
                    photo_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("PRAGMA table_info(personnel_info)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'address' not in columns:
                cursor.execute("ALTER TABLE personnel_info ADD COLUMN address TEXT")
                logger.info("已添加 address 字段")
            if 'gender' not in columns:
                cursor.execute("ALTER TABLE personnel_info ADD COLUMN gender TEXT")
                logger.info("已添加 gender 字段")
            if 'category' not in columns:
                cursor.execute("ALTER TABLE personnel_info ADD COLUMN category TEXT")
                logger.info("已添加 category 字段")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_id ON personnel_info(face_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON personnel_info(name)")
            
            conn.commit()
            logger.debug(f"数据库初始化完成: {self.db_path}")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}", exc_info=True)
            return False

    def _get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"数据库连接失败: {e}", exc_info=True)
            return None

    def get_personnel_by_face_id(self, face_id: str) -> Optional[Dict[str, Any]]:
        """根据face_id获取人员信息"""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            if not conn:
                return None

            cursor = conn.cursor()
            query = """
                SELECT name, id_number, phone, address, gender, category, status, 
                       photo_path, created_at, updated_at 
                FROM personnel_info 
                WHERE face_id = ?
            """
            cursor.execute(query, (face_id,))
            result = cursor.fetchone()

            if result:
                return {
                    "name": result["name"] if result["name"] else "",
                    "id_number": result["id_number"],
                    "phone": result["phone"],
                    "address": result["address"],
                    "gender": result["gender"],
                    "category": result["category"],
                    "status": result["status"],
                    "photo_path": result["photo_path"],
                    "created_at": result["created_at"] if result["created_at"] else None,
                    "updated_at": result["updated_at"] if result["updated_at"] else None,
                }
            return None

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"查询人员信息失败: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
