# FastAPI Docker 容器使用指南

## 容器说明

`tiangolo/uvicorn-gunicorn-fastapi:python3.10-2025-11-10` 是一个预配置的 FastAPI 运行环境，包含：
- Python 3.10
- Uvicorn (ASGI 服务器)
- Gunicorn (WSGI HTTP 服务器)
- FastAPI 框架

## 使用方法

### 1. 基本运行（当前方式）

```bash
docker run -d -p 80:80 tiangolo/uvicorn-gunicorn-fastapi:python3.10-2025-11-10
```

容器会在 `/app` 目录下查找 `main.py` 文件并自动运行。

### 2. 挂载你的代码运行

```bash
# 停止当前容器
docker stop <container_id>

# 使用卷挂载运行
docker run -d \
  -p 8000:80 \
  -v $(pwd)/fastapi-example:/app \
  tiangolo/uvicorn-gunicorn-fastapi:python3.10-2025-11-10
```

### 3. 使用环境变量配置

```bash
docker run -d \
  -p 8000:80 \
  -v $(pwd)/fastapi-example:/app \
  -e MODULE_NAME=main \
  -e VARIABLE_NAME=app \
  -e APP_MODULE=main:app \
  tiangolo/uvicorn-gunicorn-fastapi:python3.10-2025-11-10
```

### 4. 使用 docker-compose 运行

```yaml
version: '3.8'
services:
  fastapi:
    image: tiangolo/uvicorn-gunicorn-fastapi:python3.10-2025-11-10
    ports:
      - "8000:80"
    volumes:
      - ./fastapi-example:/app
    environment:
      - MODULE_NAME=main
      - VARIABLE_NAME=app
```

## 环境变量说明

- `MODULE_NAME`: Python 模块名（默认: `main`）
- `VARIABLE_NAME`: FastAPI 应用变量名（默认: `app`）
- `APP_MODULE`: 完整模块路径（默认: `main:app`）
- `WORKERS_PER_CORE`: 每个 CPU 核心的 worker 数（默认: `1`）
- `WEB_CONCURRENCY`: Web 并发数
- `HOST`: 监听地址（默认: `0.0.0.0`）
- `PORT`: 监听端口（默认: `80`）

## 访问应用

启动后访问：
- API 文档: http://localhost:8000/docs
- 替代文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## 常用操作

### 查看容器日志
```bash
docker logs <container_id>
docker logs -f <container_id>  # 实时查看
```

### 进入容器
```bash
docker exec -it <container_id> /bin/bash
```

### 重启容器
```bash
docker restart <container_id>
```

### 停止容器
```bash
docker stop <container_id>
```

## 开发建议

1. **开发模式**: 使用卷挂载，代码修改后重启容器即可生效
2. **生产模式**: 构建自定义镜像，包含所有依赖
3. **日志**: 使用 `docker logs` 查看应用日志
4. **调试**: 进入容器使用 `python -c "import main"` 测试代码

## 示例 API 端点

- `GET /` - 欢迎信息
- `GET /health` - 健康检查
- `GET /items/{item_id}` - 获取项目
- `POST /items/` - 创建项目
- `GET /info` - 系统信息

