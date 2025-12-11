# FaceSnap

基于 facenet-pytorch 的人脸检测与识别服务，提供统一的人脸检测、识别和人员信息查询 API。使用 MTCNN 进行人脸检测，使用 InceptionResnetV1 进行人脸识别。

## 功能特性

- 人脸检测：检测图片中的人脸位置
- 人脸识别：识别检测到的人脸，匹配人员信息
- 人员信息查询：返回匹配人员的详细信息（姓名、身份证号、电话）
- 统一 API：单一端点，简洁易用

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 16+（用于启动脚本）
- uv（Python 依赖管理工具）

### 安装依赖

```bash
# 安装 Python 依赖
cd backend && uv sync

# 安装 npm 依赖（用于启动脚本）
npm install
```

### 初始化数据库

```bash
npm run database:init
```

### 启动服务

```bash
# 同时启动前后端（开发模式）
npm run dev

# 仅启动后端
npm run backend

# 仅启动前端
npm run frontend
```

服务启动后访问：
- API 文档：http://localhost:8066/docs
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
