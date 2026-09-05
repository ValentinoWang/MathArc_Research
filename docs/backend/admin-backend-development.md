# MathArc 管理员端后端开发文档

状态：首期代码已落地；上线前需执行 PostgreSQL 迁移、配置受信任反向代理并完成回滚演练。

## 目标与边界

应用进程同时提供 `/admin` 页面和 `/api/admin/*` 管理接口。管理员身份由 OIDC、Cloudflare Access 或同等反向代理完成，应用只消费代理注入的四个请求头：

```text
X-Admin-Subject
X-Admin-Email
X-Admin-Role
X-Admin-Auth-Method
```

反代必须清除客户端传入的同名头。应用只有在 `MATHARC_ADMIN_TRUST_PROXY=true` 时才接受管理员请求；`matharc_access_session` 研究预览 Cookie 永远不能提升为管理员身份。

首期角色：`access_admin` 可签发/撤销邀请码，`access_reviewer` 只读，`security_admin` 还可强制失效访问会话。密码、MFA 密钥和管理员账号生命周期不由应用实现。

## 代码边界

- `matharc/v02/admin_auth.py`：代理身份解析、角色校验、管理员会话令牌哈希工具。
- `matharc/v02/admin_service.py`：PostgreSQL 领域服务、幂等和审计链。
- `matharc/v02/admin_server.py`：HTTP 路由和统一错误映射。
- `matharc/v02/access.py`：`PostgresInvitationAccessStore`，实现公网申请/兑换/会话接口的同一存储契约。
- `matharc/v02/admin_migrate.py`：旧 `access-state.json` 的只读校验和事务导入。
- `migrations/001_admin_access.sql`：正式 schema 和索引。
- `docs/prototypes/admin-console.html`：真实调用 `/api/admin/*` 的管理员页面。

## 数据模型与安全规则

迁移创建 `admin_users`、`admin_sessions`、`applications`、`invitations`、`access_sessions`、`audit_events`、`idempotency_records`。邀请码、访问令牌和管理员会话只保存 SHA-256 哈希；`topic_scopes` 使用 JSONB，并在写入前执行非空、去重和长度校验。

`invitations` 状态由 `redeemed_at`、`revoked_at` 和 `expires_at` 推导。已兑换或已撤销记录不可再次撤销。公网兑换在事务中锁定邀请码，写入 `redeemed_at` 并创建 `access_sessions`，提交失败时两个变更同时回滚。

`audit_events` 只允许插入。每条事件包含前一条事件哈希和当前事件哈希；业务变更与审计写入必须在同一事务中完成，任何审计失败都回滚业务操作。审计 payload 只放元数据和请求摘要，禁止出现 `code`、`code_hash_sha256`、`token`、密码或 MFA 秘密。

## API

认证后的读取接口：

```text
GET /api/admin/me
GET /api/admin/applications?status=PENDING&q=&page=1&page_size=25
GET /api/admin/applications/{application_id}
GET /api/admin/invitations?status=active&q=&page=1&page_size=25
GET /api/admin/access-sessions?status=ACTIVE
GET /api/admin/audit
```

列表统一返回 `{items, page, page_size, total}`。邀请码 `status` 支持 `active`、`redeemed`、`revoked`、`expired`。

写入接口：

```text
POST /api/admin/invitations
POST /api/admin/invitations/{invitation_id}/revoke
POST /api/admin/access-sessions/{session_id}/revoke
POST /api/admin/auth/logout
```

签发请求为 `email`、`topic_scopes`、`ttl_seconds`，并要求 `Idempotency-Key`。成功事务提交后才返回一次性 `code`；幂等重放返回相同邀请元数据但不恢复明文。撤销请求必须是 `{ "reason": "..." }`，原因进入审计事件。

`/api/admin/sessions` 作为旧版兼容别名继续可读；新客户端使用 `/api/admin/access-sessions`。会话状态支持 `ACTIVE`、`LOGGED_OUT`、`EXPIRED`，响应只包含元数据和推导状态。

统一状态：未认证 `401`，角色不足 `403`，参数错误 `400`，目标不存在 `404`，状态或幂等冲突 `409`，数据库/审计不可用 `500` 或 `admin_state_invalid`。`POST /api/admin/auth/login` 为代理登录兼容占位，固定返回 `401 proxy_auth_required`。

## 迁移与部署

先安装依赖并锁定版本：

```bash
uv sync --extra admin
uv lock --check
```

验证并导入旧状态（命令不会修改源 JSON）：

```bash
python -m matharc.v02.admin_migrate \
  --source /var/lib/matharc-research/access/access-state.json \
  --database-url "$MATHARC_ADMIN_DATABASE_URL" \
  --verify-only
python -m matharc.v02.admin_migrate \
  --source /var/lib/matharc-research/access/access-state.json \
  --database-url "$MATHARC_ADMIN_DATABASE_URL"
```

迁移前备份 `access-state.json` 并记录批次 ID；导入失败时保留原文件和 PostgreSQL 事务现场，不删除或覆盖源文件。切换后，`MATHARC_ADMIN_ENABLED=true` 时运行时会同时把管理员服务和公网 `AccessAPI` 指向同一 PostgreSQL DSN，保证管理员签发的邀请码可立即兑换。关闭管理员模式时继续使用原 JSON 存储。

systemd 使用 `deploy/matharc-research.env.example` 和可选的 `/etc/matharc-research/admin.env`。数据库密码通过 `LoadCredential` 或外部密钥管理器注入，不写入普通环境文件。反向代理仅转发 `/admin` 和 `/api/admin/*` 到本机应用，并负责 TLS、认证、限流和安全响应头。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v \
  tests.test_admin_auth_contract \
  tests.test_admin_api_filters \
  tests.test_postgres_access_store \
  tests.test_v02_access \
  tests.test_v02_access_server \
  tests.test_runtime_http_integration
PYTHONDONTWRITEBYTECODE=1 .venv/bin/ruff check matharc/v02 tests/test_admin_*.py
.venv/bin/python -m mypy --strict matharc/v02/admin_auth.py matharc/v02/admin_service.py matharc/v02/admin_server.py matharc/v02/admin_migrate.py
node --check docs/prototypes/admin-console.html
```

真实 PostgreSQL 测试通过 `MATHARC_TEST_DATABASE_URL` 指定隔离数据库。浏览器验收必须分别记录 API、持久化、权限和视觉证据；截图本身不代表生产部署完成。
