# Phase 0 详细设计：项目骨架

## 1. Phase 目标

Phase 0 的目标是建立 MAGE-Doc 的最小可运行工程骨架，为后续 PDF 上传、解析、证据图和 Agentic RAG 打基础。

本阶段完成后，应具备：

- FastAPI 后端基础项目。
- Next.js 前端基础项目。
- 统一配置文件。
- Docker Compose 本地编排。
- README 快速启动说明。
- 后端 `/health` 接口。
- 前端首页可以展示项目定位，并调用后端健康检查。

## 2. 非目标

本阶段不实现：

- PDF 上传。
- 数据库表。
- 页面渲染。
- PDF 解析。
- Agent 工作流。
- 检索和向量库。
- 评测系统。

这些内容从 Phase 1 开始逐步加入。

## 3. 用户可见结果

用户可以：

1. 进入 `backend` 启动 FastAPI。
2. 进入 `frontend` 启动 Next.js。
3. 打开前端页面看到 MAGE-Doc 工作台占位界面。
4. 看到后端健康状态。

## 4. 技术方案

### 4.1 后端

使用：

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic Settings
- SQLAlchemy 预留
- Pytest
- Ruff

后端模块：

```text
backend/
  pyproject.toml
  app/
    __init__.py
    main.py
    api/
      __init__.py
      health.py
    core/
      __init__.py
      config.py
    tests/
      test_health.py
```

`/health` 返回：

```json
{
  "status": "ok",
  "service": "mage-doc-backend",
  "version": "0.1.0"
}
```

### 4.2 前端

使用：

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

前端模块：

```text
frontend/
  package.json
  next.config.mjs
  tsconfig.json
  postcss.config.mjs
  tailwind.config.ts
  app/
    layout.tsx
    page.tsx
    globals.css
  lib/
    api.ts
  types/
    api.ts
```

首页展示：

- 项目名。
- 简短定位。
- V0 阶段列表。
- 后端健康状态。

### 4.3 Docker Compose

预留：

- `backend` service。
- `frontend` service。

V0 早期先保证本地命令运行，Docker Compose 可以作为配置骨架，不强制在 Phase 0 完成镜像构建优化。

## 5. 配置设计

`.env.example`：

```text
MAGEDOC_ENV=development
MAGEDOC_API_HOST=127.0.0.1
MAGEDOC_API_PORT=8000
MAGEDOC_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

后端配置类：

- `env`
- `api_host`
- `api_port`
- `cors_origins`
- `service_name`
- `version`

## 6. API 设计

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 服务健康检查 |
| `GET` | `/api/status` | API 状态摘要，Phase 0 可和 health 共用数据 |

## 7. 前端交互设计

首页不做营销 landing page，而是工具工作台占位：

- 顶部显示 MAGE-Doc 名称和当前阶段。
- 左侧显示 V0 Pipeline：Upload、Render、Parse、Retrieve、Ask、Cite。
- 中间显示“Document workspace”空状态。
- 右侧显示“System status”，展示后端连接状态。

## 8. 测试计划

后端：

- `pytest` 验证 `/health`。

前端：

- `npm run build` 验证 TypeScript 和生产构建。

Smoke：

- 后端能启动。
- 前端能构建。

## 9. 验收标准

- 后端测试通过。
- 前端构建通过。
- `/health` 返回 `status=ok`。
- README 中有启动命令。
- 项目目录符合后续 Phase 扩展需要。

## 10. 风险与取舍

| 风险 | 取舍 |
| --- | --- |
| 过早引入数据库和解析依赖 | Phase 0 不引入，避免骨架变重 |
| Docker 构建慢 | Phase 0 以本地运行和配置骨架为主 |
| 前端做得过重 | 只做工作台占位，不提前实现复杂 PDF viewer |

