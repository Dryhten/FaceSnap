"""
API数据模型定义
"""
from typing import Optional
from pydantic import BaseModel, Field


class FaceBox(BaseModel):
    """人脸位置框"""
    x: int = Field(..., description="左上角x坐标")
    y: int = Field(..., description="左上角y坐标")
    w: int = Field(..., description="宽度")
    h: int = Field(..., description="高度")


class PersonInfo(BaseModel):
    """人员信息"""
    name: str = Field(..., description="姓名")
    id_number: Optional[str] = Field(None, description="身份证号")
    phone: Optional[str] = Field(None, description="联系电话")
    address: Optional[str] = Field(None, description="地址")
    gender: Optional[str] = Field(None, description="性别（male/female/other）")
    status: Optional[str] = Field(None, description="状态（active/inactive）")
    photo_path: Optional[str] = Field(None, description="照片路径")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class DetectResponse(BaseModel):
    """人脸检测响应"""
    detected: bool = Field(..., description="是否检测到人脸")
    face_box: Optional[FaceBox] = Field(None, description="人脸位置框，未检测到人脸时为null")
    person_info: Optional[PersonInfo] = Field(None, description="人员信息，未识别到人员时为null")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    timestamp: float = Field(..., description="时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    timestamp: float = Field(..., description="时间戳")

