from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import os
import sys
import sqlite3
import json
import hashlib
import secrets
from pathlib import Path

app = FastAPI(
    title="FastAPI 示例应用",
    description="这是一个运行在 Docker 容器中的 FastAPI 应用示例，包含用户认证、数据库、文件上传等功能",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全配置
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
DATABASE_PATH = "/app/database.db"

# 初始化数据库
def init_db():
    """初始化 SQLite 数据库"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建项目表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            tax REAL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    init_db()
    # 确保上传目录存在
    Path("/app/uploads").mkdir(exist_ok=True)


# ==================== Pydantic 模型 ====================

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

class ItemResponse(Item):
    id: int
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ==================== 工具函数 ====================

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash

def generate_token(username: str) -> str:
    """生成简单的 token（生产环境应使用 JWT）"""
    return hashlib.sha256(f"{username}{SECRET_KEY}".encode()).hexdigest()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（简化版认证）"""
    token = credentials.credentials
    # 这里应该验证 token 并返回用户信息
    # 为了示例，我们简化处理
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users LIMIT 1")
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    return {"id": user[0], "username": user[1], "email": user[2]}


# ==================== 基础端点 ====================

@app.get("/")
async def root():
    """根路径，返回欢迎信息"""
    return {
        "message": "欢迎使用 FastAPI!",
        "status": "运行中",
        "container": "tiangolo/uvicorn-gunicorn-fastapi",
        "version": "2.0.0",
        "features": [
            "用户认证",
            "数据库操作",
            "文件上传",
            "分页查询",
            "错误处理"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "python_version": sys.version
    }


# ==================== 用户认证端点 ====================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """用户注册"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (user.username, user.email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "created_at": datetime.now().isoformat()
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    """用户登录"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (user.username,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result or not verify_password(user.password, result[1]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = generate_token(user.username)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

# ==================== 项目 CRUD 端点 ====================

@app.get("/items/", response_model=List[ItemResponse])
async def list_items(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取项目列表（支持分页和搜索）"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int):
    """读取单个项目"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return dict(row)

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: Item, current_user: dict = Depends(get_current_user)):
    """创建新项目（需要认证）"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO items (name, description, price, tax, user_id) VALUES (?, ?, ?, ?, ?)",
        (item.name, item.description, item.price, item.tax, current_user["id"])
    )
    conn.commit()
    item_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    conn.row_factory = sqlite3.Row
    row = cursor.fetchone()
    conn.close()
    
    return dict(row)

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: Item, current_user: dict = Depends(get_current_user)):
    """更新项目（需要认证）"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 检查项目是否存在且属于当前用户
    cursor.execute("SELECT user_id FROM items WHERE id = ?", (item_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="项目不存在")
    
    cursor.execute(
        "UPDATE items SET name=?, description=?, price=?, tax=? WHERE id=?",
        (item.name, item.description, item.price, item.tax, item_id)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    conn.row_factory = sqlite3.Row
    row = cursor.fetchone()
    conn.close()
    
    return dict(row)

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, current_user: dict = Depends(get_current_user)):
    """删除项目（需要认证）"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="项目不存在")


# ==================== 文件上传端点 ====================

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    # 检查文件大小（限制 10MB）
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
    
    # 保存文件
    file_path = f"/app/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)
    
    return {
        "filename": file.filename,
        "size": len(contents),
        "content_type": file.content_type,
        "path": file_path
    }

@app.get("/files/")
async def list_files():
    """列出所有上传的文件"""
    upload_dir = Path("/app/uploads")
    files = []
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    return {"files": files}

@app.get("/files/{filename}")
async def download_file(filename: str):
    """下载文件"""
    file_path = Path(f"/app/uploads/{filename}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)

# ==================== 系统信息端点 ====================

@app.get("/info")
async def get_info():
    """获取系统信息"""
    # 获取数据库统计
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM items")
    item_count = cursor.fetchone()[0]
    conn.close()
    
    return {
        "app_name": "FastAPI 示例",
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "hostname": os.getenv("HOSTNAME", "unknown"),
        "python_version": sys.version.split()[0],
        "statistics": {
            "users": user_count,
            "items": item_count
        }
    }

# ==================== 错误处理 ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "资源未找到", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )

