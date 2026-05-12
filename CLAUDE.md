# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 Playwright + AI 的闲鱼智能监控机器人。FastAPI 后端 + Vue 3 前端，支持多任务并发监控、多模态 AI 商品分析、多渠道通知推送。

**This fork is public-shareable multi-tenant** — deployed at https://goofish.lemonation.cloud. Upstream (Usagi-org) is single-admin; this fork adds workspace-token isolation so anyone can use the same URL with their own xianyu account (own cookies, own tasks, own criteria, own results), no cross-leak between visitors.

## 核心架构

```
API层 (src/api/routes/)
    ↓
服务层 (src/services/)
    ↓
领域层 (src/domain/)
    ↓
基础设施层 (src/infrastructure/)
```

关键入口：
- `src/app.py` - FastAPI 应用主入口
- `spider_v2.py` - 爬虫 CLI 入口
- `src/scraper.py` - Playwright 爬虫核心逻辑

服务层：
- `TaskService` - 任务 CRUD
- `ProcessService` - 爬虫子进程管理
- `SchedulerService` - APScheduler 定时调度
- `AIAnalysisService` - 多模态 AI 分析
- `NotificationService` - 多渠道通知（ntfy/Bark/企业微信/Telegram/Webhook）

前端 (`web-ui/`)：Vue 3 + Vite + shadcn-vue + Tailwind CSS

## 开发命令

```bash
# 后端开发
python -m src.app
# 或
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

# 前端开发
cd web-ui && npm install && npm run dev

# 前端构建
cd web-ui && npm run build

# 一键本地启动（构建前端 + 启动后端）
bash start.sh

# Docker 部署
docker compose up --build -d
```

## 爬虫命令

```bash
python spider_v2.py                          # 运行所有启用任务
python spider_v2.py --task-name "MacBook"    # 运行指定任务
python spider_v2.py --debug-limit 3          # 调试模式，限制商品数
python spider_v2.py --config custom.json     # 自定义配置文件
```

## 测试

```bash
pytest                              # 运行所有测试
pytest --cov=src                    # 覆盖率报告
pytest tests/unit/test_utils.py    # 运行单个测试文件
pytest tests/unit/test_utils.py::test_safe_get  # 运行单个测试函数
```

测试规范：文件 `tests/**/test_*.py`，函数 `test_*`

## 配置

环境变量 (`.env`)：
- AI 模型：`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL_NAME`
- 通知：`NTFY_TOPIC_URL`, `BARK_URL`, `WX_BOT_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- 爬虫：`RUN_HEADLESS`, `LOGIN_IS_EDGE`
- Web 认证：`WEB_USERNAME`, `WEB_PASSWORD`
- 端口：`SERVER_PORT`

任务配置 (`config.json`)：定义监控任务（关键词、价格范围、cron 表达式、AI prompt 文件等）

## 数据流

1. Web UI / config.json 创建任务
2. SchedulerService 按 cron 触发或手动启动
3. ProcessService 启动 spider_v2.py 子进程
4. scraper.py 使用 Playwright 抓取商品
5. AIAnalysisService 调用多模态模型分析
6. NotificationService 推送符合条件的商品
7. 结果存储：`jsonl/`（数据）、`images/`（图片）、`logs/`（日志）

## 注意事项

- AI 模型必须支持图片上传（多模态）
- Docker 部署需通过 Web UI 手动更新登录状态（`state.json`）
- 遇到滑动验证码时设置 `RUN_HEADLESS=false` 手动处理
- 生产环境务必修改默认 Web 认证密码 (本 fork 多租户模式下 `/auth/status` 是装饰, 不要依赖)

## 多租户隔离 (本 fork 独有)

实现在单文件 `src/multitenant.py` (~250 行), 通过 `contextvars.ContextVar` 把每次 HTTP 请求的 `workspace_id` 透到深层 DB/文件路径, 不改其余架构。

**核心机制**:
1. **中间件** `workspace_middleware` 拦截 `/api/*` + `/ws/*`, 解析 `gf_ws_token` HttpOnly cookie → 查 `workspaces` 表 → 拿 `workspace_id` 写入 ContextVar。首次访问 `/` 时自动建工作区 + 下发 cookie (365 天)
2. **DB 隔离**: `tasks` / `result_items` / `price_snapshots` 表加 `workspace_id` 列, `SqliteTaskRepository._find_all_sync` 等读路径按 ws filter, 写路径 stamp
3. **文件隔离**: `state/<account>.json` → `state/ws{id}__<account>.json` (闲鱼 cookie); `prompts/<keyword>_criteria.txt` → `prompts/ws{id}__<keyword>_criteria.txt` (AI 标准). 上游共享模板 `base_prompt.txt` / `macbook_criteria.txt` 留全局白名单 (`SHARED_PROMPT_FILES`)
4. **认证**: 不用 user/password。Cookie token 即权限凭据。无 UI 让用户看 token, 浏览器丢 cookie = 新工作区 (无找回机制)
5. **Scheduler 是进程全局**: `_reload_scheduler_if_needed` 用 `get_all_tasks_unscoped()` 跨 workspace 拿全表, 防止 user A 建任务清掉 B 的 cron
6. **AI 生成线程**: `TaskGenerationService.track()` 起新 thread + `asyncio.run` = ContextVar 不传。HTTP handler 捕获 `workspace_id` 显式传给 `run_ai_generation_job`, 在新线程内手动 `_current_workspace_id.set(...)`

**关键文件**:
- `src/multitenant.py` — 全部多租户逻辑 + helpers (scoped_account_filename / scoped_prompt_filename / SHARED_PROMPT_FILES)
- `src/app.py` — `app.middleware("http")(multitenant.workspace_middleware)` + `multitenant.register_routes(app)`
- `src/infrastructure/persistence/sqlite_task_repository.py` — ws filter on read/write/delete, `find_all_unscoped` for scheduler
- `src/api/routes/accounts.py` — 调用 `scoped_account_filename` + `is_filename_in_workspace`
- `src/api/routes/prompts.py` — 同上, .txt 后缀, 共享模板白名单
- `src/api/routes/tasks.py` — `GET/PUT /api/tasks/{id}/criteria` (task-aware criteria 编辑)
- `src/services/task_generation_runner.py` — `build_criteria_filename(keyword, workspace_id)` + workspace_id 参数透传

**未隔离的部分** (v1 已知 gap):
- `result_items` / `price_snapshots` 有 `workspace_id` 列但读路径未全部按 ws filter
- `logs/` / `images/` / `jsonl/` / `price_history/` 文件夹无 ws 前缀
- 实际影响: 任务 + 账号互不见 (大头堵住), 抓取结果列表/价格历史可能跨 workspace 漏

## Criteria 编辑 API (任务管理 UI)

- `GET /api/tasks/{task_id}/criteria` → `{ task_id, path, content }`
- `PUT /api/tasks/{task_id}/criteria` body `{ content }` → 覆写 task.ai_prompt_criteria_file 全文
- 安全: 通过 `service.get_task(task_id)` 走 workspace ContextVar gating, 自动确保只能编辑自己工作区的 task; 路径锁死在 `prompts/` 下防 path traversal
- 前端: `TasksTable` 每行 "查看/编辑" 按钮 (FileText icon) → `TasksView` 60vh 等宽 Textarea Dialog → 保存即生效 (spider 每次 run 重读文件)

## Results 页布局 (h-12 sticky bar + 16:9 密集卡)

- `ResultsView.vue` 单行 sticky `<header>` (`h-12 flex items-center gap-3`)
  - LEFT: `ResultsInsightsPanel` (3 KPI inline + 详细统计 Dialog 触发)
  - "全部展开/收起" 全局按钮 (默认展开)
  - divider
  - `ResultsFilterBar` (任务 select + 筛选 mode select + 已屏蔽 toggle + 排序 select + asc/desc + 4 action icons), 内部 spacer `flex-1` 把 actions 推到最右
- `ResultCard.vue`: 16:9 图, 1 行标题, 单色推荐点 (绿/琥珀/红) + 数字%, 默认行内展开 AI 推理 + 3 列价格行情 (市场均价/历史低位/差价). 优选 chop 用 jade 色
- `ResultsGrid.vue`: `gap-3 grid-cols-1 md:2 lg:3 xl:4`. 12 张 skeleton (16:9)
- 卡片高度 ~280-320px, 1080p 一屏 8-12 卡
- shadcn SelectTrigger 默认 `w-full`, 在 sticky bar 内必须 `!w-[Npx]` 强制覆盖, 否则会撑满 flex 行
