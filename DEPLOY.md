# 系统部署文档

## 系统架构

```
┌──────────────┐         ┌──────────────┐         ┌──────────┐
│   浏览器      │ ─HTTP─→ │  Nginx/代理   │ ─HTTP─→ │  FastAPI  │
│  Vue 3 SPA   │ ←────── │  (可选)       │ ←────── │  uvicorn  │
│  端口 5173   │         └──────────────┘         │  端口 8000 │
└──────────────┘                                  └──────────┘
                                                          │
                                                    ┌──────┴──────┐
                                                    │  SQLite DB   │
                                                    │  data/exam.db│
                                                    └─────────────┘
```

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 + Vite | 3.5+ / 6.0+ |
| 后端 | FastAPI + uvicorn | 0.115+ / 0.34+ |
| 数据库 | SQLite + SQLAlchemy | 2.0+ |
| 认证 | PyJWT + bcrypt | 2.10+ / 4.2+ |
| ORM | Pydantic | 2.10+ |

## 环境要求

- **Python**: 3.12+
- **Node.js**: 18+ (npm 9+)
- **操作系统**: Linux (推荐) / macOS / Windows (开发环境)
- **内存**: 最低 1GB，推荐 2GB+
- **磁盘**: 最低 500MB

## 目录结构

```
exam-proj/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── models.py            # 数据库模型
│   ├── schemas.py           # Pydantic 模式
│   ├── auth.py              # JWT 认证
│   ├── database.py          # 数据库连接与初始化
│   ├── requirements.txt     # Python 依赖
│   └── routers/             # API 路由
│       ├── auth.py          # 登录接口
│       ├── questions.py     # 题库管理
│       ├── papers.py        # 试卷管理
│       ├── exams.py         # 考试流程
│       ├── grading.py       # 阅卷管理
│       └── users.py         # 用户管理 + Profile
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── router.js
│       ├── api.js
│       ├── auth.js
│       ├── styles.css
│       ├── components/
│       └── views/
├── data/                    # 运行时生成 (数据库文件)
├── venv/                    # Python 虚拟环境 (自动生成)
├── logs/                    # 运行日志 (自动生成)
├── manage.ps1               # Windows 管理脚本
├── deploy.sh                # Linux 部署脚本 (支持 systemd)
└── DEPLOY.md                # 本文件
```

## 部署方式

### 方式一：开发环境部署

#### 1. 安装依赖（创建虚拟环境）

```bash
chmod +x deploy.sh
./deploy.sh install
```

脚本会自动在 `venv/` 创建 Python 虚拟环境并安装后端依赖，同时安装前端 npm 依赖。

#### 2. 启动服务

```bash
# 方式 A：使用部署脚本
./deploy.sh start

# 方式 B：分别启动
./deploy.sh backend-start
./deploy.sh frontend-start

# 方式 C：手动启动（需激活虚拟环境）
source venv/bin/activate
cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 另开终端
cd frontend && npx vite
```

#### 3. 访问

- 前端开发：http://localhost:5173
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

### 方式二：systemd 服务部署 (生产推荐)

适用于 Linux 服务器，将前后端作为系统服务管理，支持开机自启、崩溃自动重启。

#### 1. 安装依赖

```bash
./deploy.sh install
```

#### 2. 构建前端（可选，生产模式使用 PRODUCTION=1 时不需要 Vite）

```bash
./deploy.sh build
```

#### 3. 安装为系统服务

```bash
sudo ./deploy.sh svc-install
```

此命令会：
- 创建 `/etc/systemd/system/exam-backend.service` 和 `exam-frontend.service`
- 后端使用 `venv/bin/python` 运行，不受系统 Python 版本影响
- 设置 `Restart=always`，崩溃后 5 秒自动重启
- 设置开机自启 (`systemctl enable`)

#### 4. 管理服务

```bash
sudo ./deploy.sh svc-start        # 启动
sudo ./deploy.sh svc-stop         # 停止
sudo ./deploy.sh svc-restart      # 重启
sudo ./deploy.sh svc-status       # 查看状态
sudo ./deploy.sh svc-log backend  # 查看后端日志 (journalctl)
sudo ./deploy.sh svc-log frontend # 查看前端日志
sudo ./deploy.sh svc-uninstall    # 卸载服务
```

#### 5. 可选：Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 方式三：Docker 部署

```dockerfile
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend /app/frontend/dist ./frontend/dist/
ENV PRODUCTION=1
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 配置说明

配置文件：`backend/config.py`

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///data/exam.db` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `dev-secret-do-not-use-in-prod` |
| `JWT_ALGORITHM` | JWT 算法 | `HS256` |
| `JWT_EXPIRE_HOURS` | Token 有效期（小时） | `8` |

生产环境建议：
- `JWT_SECRET_KEY` 使用环境变量注入，不要硬编码
- 数据库切换为 PostgreSQL/MySQL（修改 `DATABASE_URL`）

## 数据库

### 自动初始化

首次启动时，系统自动：
1. 创建 SQLite 数据库文件 `data/exam.db`
2. 创建所有数据库表
3. 创建默认管理员账号：`admin / admin123`（角色：teacher，is_admin：true）
4. 对已有数据库进行缺失字段迁移

### 备份

```bash
# 使用脚本备份
./deploy.sh backup

# 手动备份
cp data/exam.db data/exam.db.backup.$(date +%Y%m%d)

# 恢复
./deploy.sh restore
```

## 默认账号

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | teacher | 管理员（is_admin=true） |

> 生产环境请务必修改默认密码。

## API 端点概览

### 认证
- `POST /api/login` — 用户登录
- `POST /api/register` — 用户注册（teacher 角色）

### 题库管理
- `GET /api/questions/` — 题目列表（分页）
- `POST /api/questions/` — 新增题目
- `PUT /api/questions/{id}` — 编辑题目
- `DELETE /api/questions/{id}` — 删除题目
- `GET /api/questions/categories` — 科目列表
- `POST /api/questions/category` — 新增科目
- `PUT /api/questions/category/{name}` — 重命名科目
- `DELETE /api/questions/category/{name}` — 删除科目
- `POST /api/questions/import` — 批量导入题目

### 试卷管理
- `GET /api/papers/` — 试卷列表
- `POST /api/papers/` — 新建试卷
- `PUT /api/papers/{id}` — 编辑试卷
- `DELETE /api/papers/{id}` — 删除试卷
- `GET /api/papers/{id}/questions` — 试卷题目
- `POST /api/papers/{id}/build` — 组卷（随机/指定）
- `POST /api/papers/{id}/publish` — 发布试卷
- `PUT /api/papers/{id}/unpublish` — 下线试卷

### 考试流程
- `GET /api/exams/available` — 可参加的考试
- `POST /api/exams/start` — 开始考试
- `GET /api/exams/{id}/questions` — 考试题目
- `PUT /api/exams/{id}/answer` — 保存答案
- `POST /api/exams/{id}/submit` — 提交试卷

### 阅卷与成绩
- `GET /api/submissions/` — 答卷列表
- `GET /api/submissions/{id}` — 答卷详情
- `POST /api/submissions/{id}/publish` — 发布成绩
- `GET /api/submissions/{id}/grade` — 阅卷详情
- `PUT /api/grades/{question_id}` — 主观题评分
- `GET /api/results` — 学生成绩查询

### 用户管理 (admin)
- `GET /api/users/` — 用户列表
- `POST /api/users/` — 创建用户
- `PUT /api/users/{id}` — 编辑用户
- `DELETE /api/users/{id}` — 删除用户
- `GET /api/users/template` — 下载 CSV 模板
- `POST /api/users/import` — CSV 批量导入

### 个人设置 (所有用户)
- `GET /api/users/profile` — 获取个人资料
- `PUT /api/users/profile` — 更新个人资料（含改密）

## 故障排查

### 端口被占用

```bash
# 查看占用端口的进程
lsof -i :8000   # 后端
lsof -i :5173   # 前端

# 强制释放端口
./deploy.sh stop
# 或使用 systemd
sudo ./deploy.sh svc-restart
```

### 虚拟环境问题

```bash
# 重新创建虚拟环境
rm -rf venv/
./deploy.sh install

# 手动激活虚拟环境
source venv/bin/activate
python -m pip list
```

### 服务日志查看

```bash
# systemd 模式
sudo ./deploy.sh svc-log backend
sudo ./deploy.sh svc-log frontend

# nohup 模式
tail -f logs/backend.log
tail -f logs/frontend.log
```

### 前端无法连接后端

1. 确认后端已启动：`curl http://localhost:8000/api/health`
2. 检查 Vite 代理配置：`frontend/vite.config.js`
3. 检查 CORS 配置：`backend/main.py` 中的 `allow_origins`

### Token 过期

Token 默认 8 小时过期，过期后需重新登录。可在 `backend/config.py` 中调整 `JWT_EXPIRE_HOURS`。

### 数据库锁 (SQLite)

高并发场景下 SQLite 可能出现 "database is locked" 错误，建议：
1. 切换为 PostgreSQL
2. 或增加 `check_same_thread=False`（已配置）
3. 减少并发写入
