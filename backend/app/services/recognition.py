import os
import torch
import cv2
import numpy as np
from typing import Optional, Tuple
from PIL import Image
from threading import Lock
from facenet_pytorch import MTCNN, InceptionResnetV1
from app.core.config import settings


class RecognitionService:
    def __init__(self):
        self.device = torch.device(settings.DEVICE)
        self.threshold = settings.FACE_RECOGNITION_THRESHOLD
        self.mtcnn = None
        self.model = None
        self.db_names = []
        self.db_vecs = None
        self._initialized = False
        self._lock = Lock()
    
    def initialize(self):
        if self._initialized:
            return
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # 输出设备信息
            device_str = str(self.device)
            original_device = self.device
            mtcnn_device = self.device
            
            # MTCNN 在 MUSA 设备上不支持某些操作（如 trunc），需要强制使用 CPU
            if self.device.type == 'musa':
                # MUSA GPU - MTCNN 检测使用 CPU，因为某些操作不支持
                try:
                    import torch_musa
                    if hasattr(torch, "musa") and torch.musa.is_available():
                        device_id = int(self.device.index) if self.device.index is not None else 0
                        if hasattr(torch.musa, "get_device_name"):
                            device_name = torch.musa.get_device_name(device_id)
                        else:
                            device_name = "MUSA GPU"
                        logger.info(f"MUSA GPU 设备名称: {device_name}")
                        if hasattr(torch.musa, "get_device_properties"):
                            props = torch.musa.get_device_properties(device_id)
                            if hasattr(props, "total_memory"):
                                logger.info(f"MUSA GPU 内存: {props.total_memory / 1024**3:.2f} GB")
                        # MTCNN 在 MUSA 上不支持，使用 CPU
                        mtcnn_device = torch.device('cpu')
                        logger.info("⚠️  MTCNN 检测在 MUSA 设备上不支持某些操作，将使用 CPU 进行检测")
                    else:
                        logger.warning("MUSA 设备不可用，将回退到 CPU")
                        self.device = torch.device('cpu')
                        mtcnn_device = torch.device('cpu')
                        device_str = 'cpu'
                except ImportError:
                    logger.warning("torch_musa 未安装，将回退到 CPU")
                    self.device = torch.device('cpu')
                    mtcnn_device = torch.device('cpu')
                    device_str = 'cpu'
            elif self.device.type == 'cuda':
                # CUDA GPU
                if torch.cuda.is_available():
                    logger.info(f"CUDA GPU 设备名称: {torch.cuda.get_device_name(self.device)}")
                    logger.info(f"CUDA GPU 内存: {torch.cuda.get_device_properties(self.device).total_memory / 1024**3:.2f} GB")
                else:
                    logger.warning("CUDA 设备不可用，将回退到 CPU")
                    self.device = torch.device('cpu')
                    mtcnn_device = torch.device('cpu')
                    device_str = 'cpu'
            elif self.device.type == 'cpu':
                logger.info("使用 CPU 设备")
            
            self.mtcnn = MTCNN(
                image_size=160,
                margin=20,
                device=mtcnn_device,  # 使用 mtcnn_device（MUSA 时使用 CPU）
                post_process=True
            ).eval()
            
            self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
            self._load_face_database()
            logger.info(f"识别模型已初始化 (MTCNN设备: {mtcnn_device}, 主设备: {device_str})")
            self._initialized = True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ 识别服务初始化失败: {e}", exc_info=True)
            raise
    
    def _load_face_database(self):
        import logging
        logger = logging.getLogger(__name__)
        names, vecs = [], []
        
        db_dir_str = str(settings.FACES_DIR)
        if not os.path.exists(db_dir_str):
            logger.warning(f"人脸库目录不存在: {db_dir_str}")
            return
        
        for f in os.listdir(db_dir_str):
            if f.lower().endswith(('.jpg', '.png', '.jpeg')):
                path = os.path.abspath(os.path.join(db_dir_str, f))
                try:
                    img = Image.open(path).convert('RGB')
                    face = self.mtcnn(img)
                    if face is None:
                        continue
                    
                    with torch.no_grad():
                        vec = self.model(face.unsqueeze(0).to(self.device))
                        names.append(path)
                        vecs.append(vec)
                except Exception as e:
                    logger.debug(f'跳过 {f}: {e}')
        
        if vecs:
            self.db_names = names
            self.db_vecs = torch.cat(vecs, dim=0)
            logger.info(f"已加载 {len(self.db_names)} 个人脸")
        else:
            logger.warning("人脸库为空")
    
    def recognize(self, face_img: np.ndarray) -> Optional[Tuple[str, float]]:
        """识别人脸，返回(face_id, confidence)"""
        if not self._initialized or len(self.db_names) == 0:
            return None
        
        try:
            face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            pil_face = Image.fromarray(face_rgb)
            
            with self._lock:
                face_tensor = self.mtcnn(pil_face)
                if face_tensor is None:
                    return None
                
                with torch.no_grad():
                    face_tensor_batch = face_tensor.unsqueeze(0).to(self.device)
                    vec = self.model(face_tensor_batch)
                    sims = torch.cosine_similarity(vec, self.db_vecs, dim=1)
                    best_idx = torch.argmax(sims).item()
                    best_sim = sims[best_idx].item()
                    
                    if best_sim >= self.threshold:
                        face_id = os.path.splitext(os.path.basename(self.db_names[best_idx]))[0]
                        result = (face_id, float(best_sim))
                        del face_tensor_batch, vec, sims
                        if self.device.type == 'cuda':
                            torch.cuda.empty_cache()
                        return result
                
                if self.device.type == 'cuda':
                    torch.cuda.empty_cache()
            
            return None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"人脸识别失败: {e}", exc_info=True)
            return None
    
    def add_face(self, face_img: np.ndarray) -> Optional[str]:
        """添加人脸到数据库，返回face_id"""
        if not self._initialized:
            return None
        
        try:
            import logging
            import uuid
            logger = logging.getLogger(__name__)
            
            face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            pil_face = Image.fromarray(face_rgb)
            face_tensor = self.mtcnn(pil_face)
            if face_tensor is None:
                logger.warning("无法提取人脸特征")
                return None
            
            with torch.no_grad():
                face_tensor_batch = face_tensor.unsqueeze(0).to(self.device)
                vec = self.model(face_tensor_batch)
            
            face_id = str(uuid.uuid4())
            photo_path = settings.FACES_DIR / f"{face_id}.jpg"
            pil_face.save(photo_path, "JPEG")
            
            if self.db_vecs is None:
                self.db_names = []
                self.db_vecs = vec
            else:
                self.db_names.append(str(photo_path))
                self.db_vecs = torch.cat([self.db_vecs, vec], dim=0)
            
            logger.info(f"成功添加人脸: {face_id}")
            return face_id
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"添加人脸失败: {e}", exc_info=True)
            return None
    
    def remove_face(self, face_id: str) -> bool:
        """从数据库移除人脸"""
        if not self._initialized:
            return False
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            photo_path = str(settings.FACES_DIR / f"{face_id}.jpg")
            try:
                idx = self.db_names.index(photo_path)
            except ValueError:
                logger.warning(f"未找到face_id={face_id}的人脸")
                return False
            
            if len(self.db_names) == 1:
                self.db_names = []
                self.db_vecs = None
            else:
                indices = list(range(len(self.db_names)))
                indices.remove(idx)
                self.db_vecs = self.db_vecs[indices]
                self.db_names.pop(idx)
            
            logger.info(f"成功移除人脸: {face_id}")
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"移除人脸失败: {e}", exc_info=True)
            return False
    
    def reload_face(self, face_id: str, photo_path: str) -> bool:
        """重新加载指定的人脸到数据库"""
        if not self._initialized:
            return False
        
        try:
            import logging
            from pathlib import Path
            logger = logging.getLogger(__name__)
            
            photo_path_obj = Path(photo_path) if isinstance(photo_path, str) else photo_path
            self.remove_face(face_id)
            
            if not photo_path_obj.exists():
                logger.warning(f"图片文件不存在: {photo_path_obj}")
                return False
            
            img = Image.open(photo_path_obj).convert('RGB')
            face = self.mtcnn(img)
            if face is None:
                logger.warning(f"无法从图片中提取人脸: {photo_path_obj}")
                return False
            
            with torch.no_grad():
                vec = self.model(face.unsqueeze(0).to(self.device))
            
            if self.db_vecs is None:
                self.db_names = []
                self.db_vecs = vec
            else:
                self.db_names.append(str(photo_path_obj))
                self.db_vecs = torch.cat([self.db_vecs, vec], dim=0)
            
            logger.info(f"成功重新加载人脸: {face_id}")
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"重新加载人脸失败: {e}", exc_info=True)
            return False

