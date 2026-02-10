"""
人员类别管理 API 端点
"""
from fastapi import APIRouter, HTTPException, Form
from typing import Optional, List
import logging

from app.services.personnel import PersonnelService

logger = logging.getLogger(__name__)

router = APIRouter()

personnel_service: Optional[PersonnelService] = None


def init_services(personnel: PersonnelService):
    """初始化服务实例"""
    global personnel_service
    personnel_service = personnel


@router.get("/personnel-categories", summary="获取人员类别列表")
async def get_personnel_categories():
    """
    获取所有人员类别，按 sort_order、id 排序，供下拉与类别管理页使用。
    """
    if not personnel_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    try:
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, sort_order, created_at FROM personnel_categories ORDER BY sort_order ASC, id ASC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "sort_order": row["sort_order"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取人员类别列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取人员类别列表失败: {str(e)}")


@router.post("/personnel-categories", summary="创建人员类别")
async def create_personnel_category(
    name: str = Form(..., description="类别名称"),
    sort_order: Optional[int] = Form(0, description="排序值"),
):
    """创建人员类别"""
    if not personnel_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="类别名称不能为空")
    try:
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO personnel_categories (name, sort_order) VALUES (?, ?)",
            (name, sort_order or 0),
        )
        conn.commit()
        category_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, name, sort_order, created_at FROM personnel_categories WHERE id = ?",
            (category_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return {
            "id": row["id"],
            "name": row["name"],
            "sort_order": row["sort_order"],
            "created_at": row["created_at"],
        }
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=400, detail=f"类别名称「{name}」已存在")
        logger.error(f"创建人员类别失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建人员类别失败: {str(e)}")


@router.put("/personnel-categories/{category_id}", summary="更新人员类别")
async def update_personnel_category(
    category_id: int,
    name: Optional[str] = Form(None, description="类别名称"),
    sort_order: Optional[int] = Form(None, description="排序值"),
):
    """更新人员类别（不提供删除）"""
    if not personnel_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    try:
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM personnel_categories WHERE id = ?", (category_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="类别不存在")
        updates = []
        params: List = []
        if name is not None:
            n = (name or "").strip()
            if not n:
                raise HTTPException(status_code=400, detail="类别名称不能为空")
            updates.append("name = ?")
            params.append(n)
        if sort_order is not None:
            updates.append("sort_order = ?")
            params.append(sort_order)
        if not updates:
            cursor.execute(
                "SELECT id, name, sort_order, created_at FROM personnel_categories WHERE id = ?",
                (category_id,),
            )
            row = cursor.fetchone()
            conn.close()
            return {
                "id": row["id"],
                "name": row["name"],
                "sort_order": row["sort_order"],
                "created_at": row["created_at"],
            }
        params.append(category_id)
        cursor.execute(
            f"UPDATE personnel_categories SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        cursor.execute(
            "SELECT id, name, sort_order, created_at FROM personnel_categories WHERE id = ?",
            (category_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return {
            "id": row["id"],
            "name": row["name"],
            "sort_order": row["sort_order"],
            "created_at": row["created_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=400, detail="类别名称已存在")
        logger.error(f"更新人员类别失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新人员类别失败: {str(e)}")
