# 原神角色图鉴 - 前端使用说明

## 功能概览

- **首页**：今日推荐、随机邂逅、数据概览
- **角色列表**：多维度筛选（元素、武器、稀有度、体型、地区、生日月份、全文搜索）
- **角色详情**：立绘、官方介绍、贰·故事、生日贺图、节日贺图、命之座
- **生日日历**：按月份查看角色生日

## 启动步骤

### 1. 导出角色数据

```bash
# 确保 MongoDB 已运行且爬虫已执行
python scripts/export_characters.py
```

产出：`data/characters.json`（含 birthday_parsed、zodiac、region、searchable_text、图片原图 URL 等增强字段）

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
# 从项目根目录运行（确保能读取 data/characters.json）
cd ..
set PYTHONPATH=backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

或（**PowerShell** 用分号 `;` 代替 `&&`）：

```powershell
cd backend; pip install -r requirements.txt; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

或分步执行：

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

（需确保 `data/` 在项目根目录，backend 会通过相对路径读取）

### 3. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## API 代理

前端 Vite 已配置 `/api` 代理到 `http://localhost:8000`，无需额外 CORS 配置。

## 技术栈

- React 18 + TypeScript
- Vite 7
- React Router v7
