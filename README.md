# 人脸检测服务

统一的人脸检测、识别和人员信息查询API服务。

## 功能特性

- ✅ 人脸检测：检测图片中的人脸位置
- ✅ 人脸识别：识别检测到的人脸，匹配人员信息
- ✅ 人员信息查询：返回匹配人员的详细信息（姓名、身份证号、电话）
- ✅ 统一API：单一端点，简洁易用
- ✅ 文件上传：支持jpg、png、bmp等图片格式

## 项目结构

```
FaceSnap/
├── backend/               # 后端目录
│   ├── app/               # 应用核心代码
│   │   ├── api/           # API路由
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           └── detect.py
│   │   ├── core/          # 核心模块
│   │   │   ├── config.py  # 配置管理
│   │   │   └── models.py  # 数据模型
│   │   ├── services/      # 业务逻辑服务
│   │   │   ├── detection.py
│   │   │   ├── recognition.py
│   │   │   └── personnel.py
│   │   └── utils/         # 工具函数
│   │       └── image.py
│   ├── config/            # 后端配置
│   │   └── settings.py    # 配置设置
│   ├── data/              # 数据目录
│   │   ├── database/      # SQLite 数据库文件目录
│   │   └── faces/         # 人脸图片存储目录
│   ├── scripts/           # 脚本目录
│   │   └── init_database.py  # 数据库初始化脚本
│   ├── pyproject.toml     # Python项目配置（uv使用）
│   ├── uv.lock            # 依赖锁定文件
│   └── .venv/             # Python虚拟环境（自动创建）
├── main.py                # FastAPI应用入口
├── package.json           # npm启动脚本配置
├── README.md              # 项目说明
└── .gitignore            # Git忽略配置
```

## 安装和配置

### 1. 环境要求

- Python 3.8+
- Node.js 16+（用于启动脚本管理）
- CUDA（可选，用于GPU加速）

### 2. 安装依赖管理工具

#### 2.1 安装 uv（Python 依赖管理）

如果尚未安装 uv：

```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2.2 安装 Node.js（启动脚本管理）

如果尚未安装 Node.js，请访问 [Node.js 官网](https://nodejs.org/) 下载安装。

### 3. 安装依赖

#### 3.1 安装 Python 依赖

使用uv安装项目依赖（需要在 backend 目录中执行）：

```bash
# 进入 backend 目录
cd backend

# 安装项目依赖
uv sync

# 或者使用pip（如果不想使用uv）
pip install -r requirements.txt
```

**注意**：`pyproject.toml` 和 `uv.lock` 位于 `backend/` 目录，虚拟环境 `.venv` 也会在 `backend/` 目录中创建。

#### 3.2 安装 npm 依赖（启动脚本）

```bash
# 安装 npm 依赖（用于启动脚本管理）
npm install
```

### 4. 初始化数据库

项目使用 SQLite 数据库。首次使用前需要初始化数据库：

```bash
# 使用 npm 命令初始化数据库（推荐）
npm run database:init

# 或者手动运行初始化脚本
cd backend
uv run python scripts/init_database.py
```

**说明**：
- 数据库文件将创建在 `backend/data/database/personnel.db`
- 如果数据库已存在，脚本会询问是否重新创建（将删除所有现有数据）
- 初始化后会创建 `personnel_info` 表结构，可以开始添加人员记录

### 5. 配置环境变量

项目使用 `.env` 文件进行配置管理。配置步骤：

```bash
# 1. 复制示例配置文件
cp .env.example .env

# 2. 编辑 .env 文件，修改相应的配置值
# Windows可以使用记事本或其他编辑器
notepad .env
```

**重要配置项说明**：

- **数据库配置**：SQLite 数据库路径（默认：`backend/data/database/personnel.db`，无需额外配置）
- **服务配置**：`API_HOST`, `API_PORT`
- **模型配置**：`FACE_DETECTION_THRESHOLD`, `FACE_RECOGNITION_THRESHOLD`, `DEVICE`
- **文件上传**：`MAX_UPLOAD_SIZE`（默认10MB）

**配置优先级**：
1. `.env.local`（本地覆盖配置，不会被提交到版本控制）
2. `.env`（项目配置文件）
3. 系统环境变量
4. 默认值

**注意**：
- `.env` 文件包含敏感信息，已添加到 `.gitignore`，不会被提交到版本控制
- 生产环境建议使用系统环境变量或 `.env.local` 文件

### 6. 添加人脸数据

通过 API 上传人脸图片，系统会自动：
1. 检测图片中的人脸
2. 提取人脸特征
3. 保存到 `backend/data/faces/` 目录
4. 在数据库中创建对应的人员记录

**注意**：
- 人脸图片存储在 `backend/data/faces/` 目录
- 每个上传的人脸图片会生成唯一的 `face_id`
- 需要在数据库中创建对应的人员信息记录（姓名、身份证号、电话等）

## 启动服务

### 方式1：使用 npm 启动（推荐，支持前后端同时启动）

```bash
# 首次使用需要安装 npm 依赖
npm install

# 同时启动前后端（开发模式）
npm run dev

# 只启动后端
npm run backend

# 只启动前端（前端项目创建后）
npm run frontend
```

### 方式2：使用uv运行（仅后端）

```bash
# 进入 backend 目录
cd backend

# 使用uv运行主程序（会自动激活虚拟环境）
uv run python ../main.py

# 或使用uv运行uvicorn（从 backend 目录运行，但指向根目录的 main.py）
uv run uvicorn ../main:app --host 0.0.0.0 --port 8000
```

### 方式3：激活虚拟环境后运行（仅后端）

```bash
# 进入 backend 目录
cd backend

# 激活uv创建的虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

# 然后运行
python main.py
```

### 方式3：直接运行（需要先安装依赖）

```bash
python main.py
```

服务启动后，访问：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## API使用

### 端点

**POST** `/api/v1/detect`

### 请求

- **Content-Type**: `multipart/form-data`
- **参数**: `file` (图片文件)

### 响应格式

**成功响应（检测到人脸）**:
```json
{
  "detected": true,
  "face_box": {
    "x": 100,
    "y": 150,
    "w": 200,
    "h": 200
  },
  "person_info": {
    "name": "张三",
    "id_number": "110101199001011234",
    "phone": "13800138000"
  }
}
```

**成功响应（未检测到人脸）**:
```json
{
  "detected": false,
  "face_box": null,
  "person_info": null
}
```

**成功响应（检测到人脸但未识别到人员）**:
```json
{
  "detected": true,
  "face_box": {
    "x": 100,
    "y": 150,
    "w": 200,
    "h": 200
  },
  "person_info": null
}
```

### 使用示例

#### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/detect" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/image.jpg"
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/detect"
with open("image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    print(response.json())
```

#### JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/v1/detect', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 开发

详细的开发规范请参考 [DEVELOPMENT.md](DEVELOPMENT.md)

### 代码结构说明

- **app/api/**: API路由层，处理HTTP请求和响应
- **app/services/**: 业务逻辑层，包含检测、识别、人员查询等核心功能
- **app/core/**: 核心模块，配置管理和数据模型
- **app/utils/**: 工具函数，通用功能

### 运行测试

```bash
# 运行应用
uv run main.py

# 在另一个终端测试API
curl -X POST "http://localhost:8000/api/v1/detect" \
  -F "file=@test_image.jpg"
```

## 注意事项

1. **首次启动**：服务启动时会加载模型和人脸数据库，可能需要一些时间
2. **GPU支持**：如果有NVIDIA GPU，设置 `DEVICE=cuda:0` 可以加速处理
3. **文件大小限制**：默认最大上传文件大小为10MB，可在配置中修改
4. **数据库**：首次使用前需要运行 `npm run database:init` 初始化数据库
5. **人脸数据**：通过 API 上传人脸图片，系统会自动保存到 `backend/data/faces/` 目录

## 故障排查

### 问题：服务启动失败

- 检查Python版本和依赖是否安装完整
- 检查CUDA和PyTorch是否正确安装（如果使用GPU）

### 问题：无法识别人员

- 检查 `data/face_db/` 目录中是否有对应的人脸图片
- 检查数据库中是否有对应的 `personnel_info` 记录
- 检查 `face_id` 是否匹配（文件名不含扩展名）

### 问题：数据库连接失败

- 检查数据库文件路径是否正确（默认：`backend/data/restore/personnel.db`）
- 检查数据库文件权限
- 检查数据库文件是否损坏（可以删除后重新启动服务，会自动重建）

## 版本历史

### v2.0.0
- 重构为单一统一API服务
- 简化API接口
- 优化代码结构

### v1.0.0
- 多服务架构
- 基础功能实现

## 许可证

[根据实际情况填写]

## 联系方式

[根据实际情况填写]

