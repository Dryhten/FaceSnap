# FaceSnap

基于 facenet-pytorch 的人脸检测与识别服务，提供统一的人脸检测、识别和人员信息查询 API。使用 MTCNN 进行人脸检测，使用 InceptionResnetV1 进行人脸识别。

## 功能特性

- 人脸检测：检测图片中的人脸位置
- 人脸识别：识别检测到的人脸，匹配人员信息
- 人员信息查询：返回匹配人员的详细信息（姓名、身份证号、电话）
- 统一 API：单一端点，简洁易用

## 快速开始

### MUSA 部署

MUSA GPU 推荐使用 Docker 容器方式部署，容器内已配置好 conda 环境。

#### 一、环境准备

```bash
# 1. 更新系统包列表
sudo apt update

# 2. 安装 Python pip（如果已安装可跳过）
sudo apt install python3-pip -y

# 3. 安装 Node.js 和 npm（如果已安装可跳过）
# 方法1：使用 NodeSource 官方仓库（推荐，可安装最新版本）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 方法2：使用系统包管理器（版本可能较旧）
# sudo apt install -y nodejs npm

# 验证安装
node --version
npm --version

# 4. 安装官方 musa-deploy 工具
sudo pip install musa-deploy -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

#### 二、一键拉起 Torch_MUSA 开发 & 推理的 docker 容器

```bash
sudo musa-deploy --demo torch_musa \
                 --name facesnap \
                 -v /home/server:/home/server \
                 --network host \
                 --pid host
```

**参数说明：**
- `--name facesnap`：容器名称，可自定义
- `-v /home/server:/home/server`：将主机项目目录挂载进容器（请根据实际路径修改）
- `--network host --pid host`：推荐加上，便于后续调试和性能最优
- `--force`：如果已安装驱动但版本不兼容，加上此参数可强制更换驱动到目标容器适配的版本

**注意事项：**
- 如果已经安装了驱动，运行以上命令报驱动版本不兼容的问题，需要加上 `--force` 参数，系统会自动回退到兼容的驱动版本
- 安装到一半会提示重启服务器，启动完服务器再运行一次这个命令
- 没提示重启服务器就安装结束的，可以直接进入下一步（因为你装过这个容器所需的目标驱动了）

#### 三、进入容器并完成环境补全

```bash
# 进入docker容器，会自动激活conda环境
sudo docker exec -it facesnap bash
```

在容器内执行以下命令安装视觉模型相关依赖：

```bash
# 安装视觉模型相关依赖
apt update && apt install -y libgl1-mesa-glx libglib2.0-0
conda install -c conda-forge libstdcxx-ng=13 -y
```

#### 四、安装项目依赖

在容器内执行：

```bash
# 进入项目目录（根据实际挂载路径调整）
cd /home/server/FaceSnap

# 安装前后端依赖（会自动处理 facenet-pytorch 的依赖问题）
npm run install:musa
```

或者手动安装：

```bash
# 安装后端依赖
cd backend
pip install -r requirements_musa.txt
pip install --no-deps 'facenet-pytorch>=2.5.3'

# 安装前端依赖
cd ../frontend
npm install
```

**重要提示：** 使用 `--no-deps` 标志意味着您要对 `torch` 和 `torchvision` 的可用性负责。您必须确保在运行应用程序之前，兼容版本的 `torch` 和 `torchvision` 已经通过其他方式（例如使用 conda 或其他 pip 命令）安装在您的环境中。

#### 五、初始化数据库

在容器内执行：

```bash
cd /home/server/FaceSnap
npm run database:init:musa
```

或者手动执行：

```bash
cd /home/server/FaceSnap/backend
python scripts/init_database.py
```

#### 六、配置环境变量

在容器内复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# ==================== 后端服务配置 ====================
API_HOST=0.0.0.0
API_PORT=8066
API_RELOAD=false

# ==================== 后端模型配置 ====================
FACE_DETECTION_THRESHOLD=0.9
FACE_RECOGNITION_THRESHOLD=0.7
# 设备配置：auto 或不填则自动检测（优先使用 GPU），也可手动指定 cuda:0 / musa:0 / cpu
# DEVICE=auto

# ==================== 后端文件上传配置 ====================
MAX_UPLOAD_SIZE=10485760
ALLOWED_IMAGE_EXTENSIONS=.jpg,.jpeg,.png,.bmp

# ==================== 后端日志配置 ====================
LOG_LEVEL=INFO
```

#### 七、运行服务

在容器内执行：

```bash
# 进入项目根目录
cd /home/server/FaceSnap

# 方式1：同时启动前后端（开发模式）
npm run dev:musa

# 方式2：仅启动后端
npm run backend:musa

# 方式3：仅启动前端
npm run frontend

# 方式4：直接运行（不使用 npm 脚本）
cd backend
python run.py
```

服务启动后，访问：
- API 文档（Swagger UI）：http://localhost:8066/docs
- API 文档（ReDoc）：http://localhost:8066/redoc
- 健康检查：http://localhost:8066/health

---

### CUDA 部署

#### 一、环境要求

- Python >= 3.12
- PyTorch >= 2.0.0（带 CUDA 支持）
- CUDA 驱动和工具包（根据 PyTorch 版本要求）
- Node.js 16+ 和 npm（用于启动脚本）
- uv（Python 依赖管理工具）

#### 二、安装 Node.js 和 npm（如果未安装）

```bash
# 方法1：使用 NodeSource 官方仓库（推荐，可安装最新版本）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 方法2：使用系统包管理器（版本可能较旧）
# sudo apt install -y nodejs npm

# 验证安装
node --version
npm --version
```

#### 三、安装依赖

```bash
# 进入后端目录
cd backend

# 使用 uv 安装依赖
uv sync
```

#### 四、初始化数据库

```bash
# 在项目根目录执行
npm run database:init
```

或者：

```bash
cd backend
uv run python scripts/init_database.py
```

#### 五、配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# ==================== 后端服务配置 ====================
API_HOST=0.0.0.0
API_PORT=8066
API_RELOAD=false

# ==================== 后端模型配置 ====================
FACE_DETECTION_THRESHOLD=0.9
FACE_RECOGNITION_THRESHOLD=0.7
# 设备配置：CUDA 使用 cuda:0，MUSA GPU 使用 musa:0，CPU 使用 cpu
DEVICE=cuda:0

# ==================== 后端文件上传配置 ====================
MAX_UPLOAD_SIZE=10485760
ALLOWED_IMAGE_EXTENSIONS=.jpg,.jpeg,.png,.bmp

# ==================== 后端日志配置 ====================
LOG_LEVEL=INFO
```

#### 六、运行服务

```bash
# 方式1：同时启动前后端（开发模式）
npm run dev

# 方式2：仅启动后端
npm run backend

# 方式3：直接运行（不使用 npm 脚本）
cd backend
uv run python run.py

# 方式4：使用 uvicorn 直接运行
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8066
```

服务启动后，访问：
- API 文档（Swagger UI）：http://localhost:8066/docs
- API 文档（ReDoc）：http://localhost:8066/redoc
- 健康检查：http://localhost:8066/health

## API 使用

### 端点

**POST** `/api/v1/detect`

### 请求

- **Content-Type**: `multipart/form-data`
- **参数**: `file` (图片文件)

### 响应格式

**检测到人脸并识别成功**:
```json
{
  "detected": true,
  "face_box": {"x": 100, "y": 150, "w": 200, "h": 200},
  "person_info": {
    "name": "张三",
    "id_number": "110101199001011234",
    "phone": "13800138100"
  }
}
```

**检测到人脸但未识别**:
```json
{
  "detected": true,
  "face_box": {"x": 100, "y": 150, "w": 200, "h": 200},
  "person_info": null
}
```

**未检测到人脸**:
```json
{
  "detected": false,
  "face_box": null,
  "person_info": null
}
```

### 使用示例

```bash
curl -X POST "http://localhost:8066/api/v1/detect" \
  -F "file=@image.jpg"
```

## 项目结构

```
FaceSnap/
├── backend/              # 后端代码
│   ├── app/             # 应用核心
│   │   ├── api/v1/      # API 路由
│   │   ├── services/    # 业务逻辑
│   │   ├── core/        # 配置和模型
│   │   └── utils/       # 工具函数
│   ├── data/            # 数据目录
│   │   ├── database/    # SQLite 数据库
│   │   └── faces/       # 人脸图片存储
│   └── scripts/         # 脚本
├── frontend/            # 前端代码
└── main.py              # FastAPI 应用入口
```

## 技术栈

- **后端**: FastAPI, PyTorch, MTCNN, InceptionResnetV1
- **前端**: React 18+, TypeScript, Vite
- **数据库**: SQLite
- **依赖管理**: uv (Python), npm (Node.js)

## 注意事项

1. 首次启动时会加载模型，可能需要一些时间
2. 支持 GPU 加速（设置 `DEVICE=cuda:0`）
3. 默认最大上传文件大小为 10MB
4. 首次使用前需运行 `npm run database:init` 初始化数据库
