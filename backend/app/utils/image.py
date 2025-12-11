import cv2
import numpy as np
from typing import Optional


def decode_image_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """从字节数据解码图像"""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        print(f"图像解码失败: {e}")
        return None


def validate_image(image: np.ndarray) -> bool:
    """验证图像是否有效"""
    if image is None:
        return False
    if image.size == 0:
        return False
    if len(image.shape) != 3:
        return False
    if image.shape[0] < 20 or image.shape[1] < 20:
        return False
    return True

