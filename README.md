# 在线考试系统

一个轻量级的在线考试系统，采用 Vue 3 + FastAPI + SQLite 构建。支持教师题库管理、组卷、考试发布、学生在线答题、自动批改以及教师手动评分等完整考试流程。

## 功能概览

### 教师端
- **题库管理** — 单选题、多选题、填空题、简答题的增删改查；文本批量导入；分类筛选
- **试卷构建** — 创建试卷，按指定题目ID或随机策略添加题目，支持排序和删除
- **考试发布** — 设置考试时间窗口和时长，发布/下架考试
- **阅卷** — 查看已提交答卷，手动评分简答题并添加评语，发布成绩
- **成绩总览** — 按考试筛选查看所有答卷，按总分排序，展示客观分/主观分明细

### 学生端
- **考试列表** — 浏览当前时间窗口内可参加的考试
- **在线答题** — 答题过程中自动保存答案；支持计时器；完成后交卷
- **成绩查询** — 查看已公布的成绩及每道题的反馈

## 技术栈

**后端：**
- Python 3.12+ / FastAPI / SQLAlchemy / SQLite
- JWT 认证 (PyJWT) / bcrypt
- 自定义文本解析器，支持题目批量导入

**前端：**
- Vue 3 (Composition API, `<script setup>`)
- Vue Router / Axios / Vite

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npx vite --port 5173
```

### 使用管理脚本

```powershell
.\manage.ps1 start     # 启动前后端服务
.\manage.ps1 stop      # 停止所有服务
.\manage.ps1 restart   # 重启所有服务
.\manage.ps1 status    # 查看服务状态
```

- 后端地址: http://localhost:8000 (接口文档 `/docs`)
- 前端地址: http://localhost:5173

### 默认账号
- 教师: `teacher` / `teacher123`
- 学生: `student` / `student123`

## 项目结构

```
exam-proj/
├── manage.ps1                  # 服务管理脚本
├── backend/
│   ├── main.py                 # FastAPI 应用入口
│   ├── models.py               # SQLAlchemy 数据模型
│   ├── schemas.py              # Pydantic 数据校验
│   ├── database.py             # 数据库引擎和会话
│   ├── config.py               # 配置文件
│   ├── auth.py                 # JWT 认证和密码工具
│   ├── routers/
│   │   ├── auth.py             # 登录、注册
│   │   ├── questions.py        # 题目 CRUD 和导入
│   │   ├── papers.py           # 试卷 CRUD 和发布
│   │   ├── exams.py            # 考试会话和答题提交
│   │   └── grading.py          # 阅卷、评分、成绩查询
│   └── services/
│       ├── question_parser.py  # 文本格式题目解析器
│       └── exam_engine.py      # 组卷引擎(指定/随机)
│       └── grading_engine.py   # 自动批改引擎
└── frontend/
    ├── src/
    │   ├── main.js             # Vue 应用入口
    │   ├── router.js           # Vue Router 路由配置
    │   ├── api.js              # Axios 实例
    │   ├── auth.js             # 前端认证工具
    │   ├── components/
    │   │   └── NavBar.vue      # 基于角色的导航栏
    │   └── views/
    │       ├── Login.vue       # 登录页
    │       ├── teacher/
    │       │   ├── QuestionBank.vue    # 题库管理
    │       │   ├── PaperBuilder.vue    # 试卷构建
    │       │   ├── ExamManager.vue     # 考试发布
    │       │   ├── Submissions.vue     # 答卷列表
    │       │   ├── Grading.vue         # 阅卷详情
    │       │   └── Grades.vue          # 成绩总览
    │       └── student/
    │           ├── ExamList.vue        # 考试列表
    │           ├── ExamView.vue        # 在线答题
    │           └── Results.vue         # 成绩查询
    └── package.json
```

## API 接口

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/login` | 登录 |
| POST | `/api/register` | 注册(仅教师可操作) |

### 题库
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/questions` | 题目列表(可选 `?category=` 筛选) |
| POST | `/api/questions` | 新建题目(教师) |
| GET | `/api/questions/{id}` | 题目详情 |
| PUT | `/api/questions/{id}` | 更新题目(教师) |
| DELETE | `/api/questions/{id}` | 删除题目(教师) |
| POST | `/api/questions/import` | 批量导入题目(教师) |

### 试卷
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/papers` | 试卷列表 |
| POST | `/api/papers` | 创建试卷(教师) |
| GET | `/api/papers/{id}` | 试卷详情 |
| GET | `/api/papers/{id}/questions` | 试卷中的题目 |
| PUT | `/api/papers/{id}` | 更新试卷(教师) |
| DELETE | `/api/papers/{id}` | 删除试卷(仅草稿状态, 教师) |
| POST | `/api/papers/{id}/build` | 向试卷中添加题目(教师) |
| POST | `/api/papers/{id}/publish` | 发布试卷，设置时间窗口(教师) |
| PUT | `/api/papers/{id}/unpublish` | 下架试卷(教师) |
| DELETE | `/api/papers/{id}/questions/{pq_id}` | 从试卷中移除某道题目 |
| POST | `/api/papers/{id}/questions/clear` | 清空试卷中的所有题目 |

### 考试
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/exams/available` | 学生可查看的可用考试列表 |
| POST | `/api/exams/start` | 开始考试(创建会话) |
| GET | `/api/exams/{session_id}/questions` | 获取考试题目 |
| PUT | `/api/exams/{session_id}/answer` | 保存答案(考试中自动保存) |
| POST | `/api/exams/{session_id}/submit` | 交卷(触发自动批改) |

### 阅卷与成绩
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/submissions` | 答卷列表(可选 `?paper_id=` 筛选) |
| GET | `/api/submissions/{id}/detail` | 答卷详情(含所有答案) |
| POST | `/api/answers/{id}/score` | 为简答题评分(教师) |
| POST | `/api/submissions/{id}/publish` | 发布成绩(教师) |
| GET | `/api/results` | 已发布成绩列表(学生) |
| GET | `/api/results/{session_id}` | 成绩详情(学生) |

## 评分逻辑

- **客观题分 (auto_score)** — 学生交卷时自动批改，涵盖单选、多选、填空题。由 `grading_engine.py` 计算。
- **主观题分 (manual_score)** — 教师手动为简答题逐题评分后累加。未评分时默认为 0。
- **总分 (total_score)** — `客观题分 + 主观题分`，每次主观题评分后和发布时自动重新计算。

## 题目批量导入格式

粘贴以下格式的文本即可批量导入题目：

```
[Q] 牛顿第一定律的内容是什么？
[A] 任何物体都要保持匀速直线运动或静止状态...
[P] 10

[Q] 下列哪些是向量？
[O] 速度, 速度, 加速度, 质量
[A] 速度, 加速度
[P] 5
```

解析器会根据内容结构自动识别题目类型（有选项的为选择题，含 `___` 的为填空题，其余为简答题）。
