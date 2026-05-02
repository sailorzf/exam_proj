# 在线考试系统 — 产品需求文档 (PRD)

## 1. 概述

### 1.1 产品定位
一款轻量级在线考试系统，面向教师和学生两类用户，覆盖**题库管理 → 组卷 → 发布考试 → 在线答题 → 自动批改 → 人工评分 → 成绩发布**的完整流程。

### 1.2 技术栈
| 层 | 技术 |
|----|------|
| 前端 | Vue 3 (Composition API) + Vue Router + Axios + Vite |
| 后端 | Python FastAPI + SQLAlchemy + SQLite |
| 认证 | JWT (PyJWT) + bcrypt 密码加密 |
| 部署 | 开发环境: `uvicorn --reload` + `vite`; 生产: 构建前端静态文件，后端直接 serve |

### 1.3 核心约束
- 单用户、单实例部署，无第三方依赖
- SQLite 作为存储，适合百~千人量级
- 前后端分离开发，生产合并为单进程

---

## 2. 用户角色

| 角色 | 说明 |
|------|------|
| 教师 (teacher) | 管理题库、组卷、发布考试、阅卷、查看成绩 |
| 学生 (student) | 查看可参加的考试、在线答题、查看已发布的成绩 |
| 管理员 | 暂无独立角色，教师具备用户注册权限 |

---

## 3. 功能需求

### 3.1 用户认证

| 编号 | 功能 | 说明 |
|------|------|------|
| AUTH-1 | 登录 | 用户名 + 密码，返回 JWT token，有效期 8 小时 |
| AUTH-2 | 注册 | 仅教师可操作，指定角色(teacher/student)，密码 bcrypt 加密 |
| AUTH-3 | 权限隔离 | 学生不可访问教师页面，反之亦然；路由守卫 + 后端权限校验 |

### 3.2 题库管理 (教师)

| 编号 | 功能 | 说明 |
|------|------|------|
| QB-1 | 题目类型 | 单选题、多选题、填空题、简答题 |
| QB-2 | 新建题目 | 填写类型、题干、选项(选择题)、参考答案、分值、分类 |
| QB-3 | 编辑题目 | 可修改所有字段 |
| QB-4 | 删除题目 | 教师可删除题目 |
| QB-5 | 分类筛选 | 按 category 字段过滤展示 |
| QB-6 | 批量导入 | 粘贴文本格式，系统自动解析类型并入库 |

**导入格式示例：**
```
Q1. 牛顿第一定律的内容是什么？
A: 物体保持静止或匀速直线运动...

Q2. 下列哪些是向量？(多选)
A. 速度
B. 质量
C. 加速度
D. 力
A: A,C,D
```

### 3.3 试卷管理 (教师)

| 编号 | 功能 | 说明 |
|------|------|------|
| PB-1 | 创建试卷 | 填写标题、描述，初始状态为 draft |
| PB-2 | 指定题目组卷 | 从题库中选择题目的 ID 列表，按序加入试卷 |
| PB-3 | 随机组卷 | 指定数量和分类标签，从题库随机抽取 |
| PB-4 | 移除题目 | 从试卷中移除某道题目 |
| PB-5 | 清空试卷 | 一键清空已选题目 |
| PB-6 | 编辑试卷 | 修改标题、描述 |
| PB-7 | 删除试卷 | 仅限 draft 状态的试卷 |
| PB-8 | 发布试卷 | 设置考试起止时间窗口 + 考试时长，状态变为 active |
| PB-9 | 下架试卷 | 将 active 试卷设为 offline，学生不可见 |

### 3.4 考试管理 (教师)

| 编号 | 功能 | 说明 |
|------|------|------|
| EM-1 | 查看已发布考试 | 展示所有试卷及其状态(草稿/已发布/已下架) |
| EM-2 | 一键发布 | 弹出表单，填写时间窗口和时长后发布 |
| EM-3 | 下架操作 | 将已发布的考试下架 |

### 3.5 答卷管理 (教师)

| 编号 | 功能 | 说明 |
|------|------|------|
| SB-1 | 答卷列表 | 展示所有已提交答卷，按考试筛选，列: 考试轮次、学生姓名、客观题分、主观题分、总分 |
| SB-2 | 状态展示 | 答题中 / 已交卷 / 成绩已公布(中文) |
| SB-3 | 阅卷入口 | 点击"阅卷"进入阅卷详情页 |
| SB-4 | 阅卷详情 | 展示该答卷所有题目及答案，顶部显示: 考试名-学生名、客观分、主观分、总分 |
| SB-5 | 题目筛选 | 可按全部/客观题/主观题筛选显示 |
| SB-6 | 主观题评分 | 简答题得分可编辑，调用接口保存，总分实时更新 |
| SB-7 | 成绩发布 | 点击发布按钮，状态变为"成绩已公布"，可重复发布(幂等) |

### 3.6 成绩总览 (教师)

| 编号 | 功能 | 说明 |
|------|------|------|
| GR-1 | 成绩列表 | 展示所有答卷，按考试筛选 |
| GR-2 | 排序 | 按总分降序排列 |
| GR-3 | 展示列 | 考试轮次、学生姓名、客观分、主观分、总分 |

### 3.7 在线答题 (学生)

| 编号 | 功能 | 说明 |
|------|------|------|
| EX-1 | 考试列表 | 展示当前时间窗口内 active 状态的考试 |
| EX-2 | 开始考试 | 创建 ExamSession，进入答题页面 |
| EX-3 | 题目展示 | 按顺序显示题目及选项(选择题)/输入框(填空)/文本域(简答) |
| EX-4 | 答案保存 | 实时保存答案，PUT 接口支持更新 |
| EX-5 | 交卷 | 提交试卷，触发自动批改引擎 |
| EX-6 | 计时器 | 显示剩余时间，超时自动交卷 |

### 3.8 成绩查询 (学生)

| 编号 | 功能 | 说明 |
|------|------|------|
| RS-1 | 已发布成绩列表 | 仅展示 status = published 的考试 |
| RS-2 | 成绩详情 | 查看每道题的学生答案、正确答案(主观题不显示)、得分、教师评语 |

---

## 4. 数据模型

### 4.1 ER 关系图

```
User 1 ────< Paper 1 ────< PaperQuestion >──── 1 Question
  │              │                                    │
  │              │                                    │
  └───< ExamSession >───< Answer ─────────────────────┘
```

### 4.2 表结构

**users**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| username | STRING UNIQUE | 登录名 |
| password_hash | STRING | bcrypt |
| role | STRING | teacher / student |
| created_at | DATETIME | |

**questions**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| type | STRING | choice_single / choice_multi / fill_blank / essay |
| question_text | TEXT | 题干 |
| options | TEXT | JSON 数组(选择题) |
| answer_text | TEXT | 参考答案 |
| points | INT | 分值, 默认 5 |
| category | STRING | 分类标签 |
| created_by | INT FK → users | |
| created_at | DATETIME | |

**papers**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| title | STRING | |
| description | TEXT | |
| created_by | INT FK → users | |
| status | STRING | draft / active / offline |
| window_start | DATETIME | 考试开始时间 |
| window_end | DATETIME | 考试结束时间 |
| duration_minutes | INT | 考试时长(分钟) |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**paper_questions**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| paper_id | INT FK → papers | |
| question_id | INT FK → questions | |
| order_index | INT | 题目顺序 |
| custom_points | INT | 自定义分值(可为空) |

**exam_sessions**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| student_id | INT FK → users | |
| paper_id | INT FK → papers | |
| start_time | DATETIME | 开始时间 |
| submit_time | DATETIME | 提交时间 |
| status | STRING | in_progress / submitted / published |
| auto_score | FLOAT | 客观题自动评分 |
| manual_score | FLOAT | 主观题人工评分 |
| total_score | FLOAT | 总分 |

**answers**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| session_id | INT FK → exam_sessions | |
| question_id | INT FK → questions | |
| paper_question_id | INT FK → paper_questions | 可为空 |
| student_answer | TEXT | 学生答案 |
| is_correct | BOOL | 是否正确(客观题) |
| score | FLOAT | 得分 |
| teacher_comment | TEXT | 教师评语 |

---

## 5. 业务规则

### 5.1 自动批改规则 (`grading_engine.py`)

| 题型 | 批改逻辑 |
|------|---------|
| 单选题 | 字符串完全匹配 |
| 多选题 | 拆分为集合后比对(逗号分隔，忽略空格) |
| 填空题 | 归一化比对(去空格、标点、转小写) |
| 简答题 | 不自动批改，`score` 保持 null，待教师手动评分 |

### 5.2 评分计算

```
auto_score   = Σ(客观题得分)        — 交卷时自动计算
manual_score = Σ(简答题手动得分)    — 教师逐题评分后汇总，默认 0
total_score  = auto_score + manual_score
```

### 5.3 考试状态流转

```
Paper:  draft →(发布)→ active →(下架)→ offline
Session: in_progress →(交卷)→ submitted →(发布)→ published
```

### 5.4 权限控制

- 题库/试卷/发布/答卷/阅卷/成绩 页面 — 仅教师可访问
- 考试列表/答题/成绩查询 页面 — 仅学生可访问
- 注册接口 — 需教师 token
- 所有写操作 — 后端校验 token 角色

### 5.5 安全策略

- 密码: bcrypt 加密存储
- Token: JWT HS256，8 小时过期
- CORS: 仅允许前端开发服务器 `http://localhost:5173`
- 学生只能查看自己的答卷和成绩

---

## 6. 非功能需求

| 指标 | 要求 |
|------|------|
| 并发用户 | 百级(单实例 SQLite) |
| 题库容量 | 千~万级题目 |
| 响应时间 | API < 500ms (本地) |
| 浏览器 | 现代浏览器(Chrome/Firefox/Edge) |
| 数据持久化 | SQLite 文件 `backend/data/exam.db` |

---

## 7. 前端路由结构

```
/login                          — 登录页
/teacher/                       — 教师布局(重定向到 questions)
  /teacher/questions            — 题库管理
  /teacher/papers               — 试卷管理
  /teacher/exams                — 考试发布
  /teacher/submissions          — 答卷列表
  /teacher/submissions/grade/:id — 阅卷详情
  /teacher/grades               — 成绩总览
/student/                       — 学生布局(重定向到 exams)
  /student/exams                — 考试列表
  /student/exam/:id             — 答题页面
  /student/results              — 成绩查询
```

---

## 8. 运维管理

### 8.1 服务管理脚本 (`manage.ps1`)

| 命令 | 功能 |
|------|------|
| `.\manage.ps1 start` | 启动前后端，等待就绪 |
| `.\manage.ps1 stop` | 清理端口占用进程 |
| `.\manage.ps1 restart` | 先 stop 再 start |
| `.\manage.ps1 status` | 查看端口监听状态 |

### 8.2 端口

| 服务 | 端口 |
|------|------|
| 后端 (FastAPI) | 8000 |
| 前端 (Vite) | 5173 |

---

## 9. 当前状态与后续规划

### 9.1 已完成
- [x] 用户登录/注册 + JWT 认证
- [x] 题库 CRUD + 批量导入
- [x] 试卷创建 + 指定/随机组卷
- [x] 考试发布(时间窗口 + 时长)
- [x] 学生在线答题 + 自动保存
- [x] 自动批改(单选/多选/填空)
- [x] 手动评分(简答题)
- [x] 成绩发布(教师)
- [x] 成绩查询(学生)
- [x] 成绩总览 + 答卷列表
- [x] PowerShell 服务管理脚本

### 9.2 建议后续迭代
- [ ] 考试倒计时 + 超时自动交卷
- [ ] 防作弊(切屏检测、随机乱序)
- [ ] 成绩统计分析(平均分、分数分布图)
- [ ] Excel/Word 格式题目导入
- [ ] 多教师协作(权限细分)
- [ ] 生产部署(Docker/Nginx/MySQL)
- [ ] 考试通知/提醒功能
- [ ] 答案自动保存草稿
