# MathArc 管理员 API 契约

状态：已实现首期反向代理认证适配器；PostgreSQL 迁移和真实部署仍需单独执行。

本契约来自 [`docs/prototypes/admin-console-blueprint.md`](../prototypes/admin-console-blueprint.md)。管理员控制面使用独立的 `/api/admin` 前缀和管理员会话，不得复用公网研究预览 Cookie。契约测试位于 [`tests/test_admin_auth_contract.py`](../../tests/test_admin_auth_contract.py)，使用 fake HTTP 连接，不需要 PostgreSQL。

## 认证

登录由 OIDC、Cloudflare Access 或同等反向代理完成。应用不实现密码/MFA 校验；保留 `POST /api/admin/auth/login` 兼容路径并固定返回 `401 {"error":"proxy_auth_required"}`。反代转发时必须注入完整的 `X-Admin-Subject`、`X-Admin-Email`、`X-Admin-Role`、`X-Admin-Auth-Method`，并清除客户端同名请求头。

后续请求使用受信任反向代理注入的 `X-Admin-Subject`、`X-Admin-Email`、`X-Admin-Role` 和 `X-Admin-Auth-Method`。应用仅在 `MATHARC_ADMIN_TRUST_PROXY=true` 时接受这些头；客户端自行伪造或缺失身份返回 `401`。`X-Admin-Role` 只在代理信任边界内生效，不能由请求体或查询参数覆盖。

## 路由与权限

| 方法 | 路径 | 权限 | 成功状态 |
| --- | --- | --- | --- |
| `POST` | `/api/admin/auth/logout` | 已认证 | `204` |
| `GET` | `/api/admin/me` | 已认证 | `200` |
| `GET` | `/api/admin/applications` | `admin.read` | `200` |
| `GET` | `/api/admin/applications/{id}` | `admin.read` | `200` |
| `GET` | `/api/admin/invitations` | `admin.read` | `200` |
| `POST` | `/api/admin/invitations` | `invitation.issue` | `201` |
| `POST` | `/api/admin/invitations/{id}/revoke` | `invitation.revoke` | `200` |
| `GET` | `/api/admin/access-sessions` | `admin.read` | `200` |
| `GET` | `/api/admin/audit` | `admin.read` | `200` |

第一期角色是 `access_admin`。兼容读取角色为 `access_reviewer`，安全运营角色为 `security_admin`；角色只是服务端身份映射的结果。无权限返回 `403`，未知路径返回 `404`，不允许的方法返回 `405`。

列表接口 `GET /api/admin/applications` 和 `GET /api/admin/invitations` 接受 `status`、`q`、`page`（默认 `1`）和 `page_size`（默认 `25`，范围 `1..1000`）查询参数。响应统一为 `{items, page, page_size, total}`；`total` 是应用筛选条件后的总记录数，不是当前页长度。邀请码状态筛选值为 `active`、`redeemed`、`revoked` 和 `expired`，搜索 `q` 匹配邮箱或邀请码 ID。

`GET /api/admin/access-sessions` 接受 `status=ACTIVE|LOGGED_OUT|EXPIRED`，返回访问会话元数据和推导状态。

## 写入、幂等与错误

所有写入接口都要求非空 `Idempotency-Key`。相同 key 和完全相同的请求体必须返回第一次业务结果并标记 `replayed: true`；由于邀请码明文只显示一次，幂等重放不会恢复 `code`。相同 key 搭配不同请求体返回 `409`。缺少 key 或请求字段错误返回 `400`。撤销请求必须提供非空 `reason`；撤销已兑换、已撤销或不存在的目标分别按状态返回 `409` 或 `404`。

签发请求字段为 `email`、`topic_scopes`、`expires_in_seconds`、`mfa_code`。签发响应可以包含一次性 `code`，但服务端存储、审计记录、列表和异常消息不得包含邀请码明文或 `code_hash_sha256`。

## 响应脱敏

列表和审计响应只能返回业务所需的元数据。以下字段禁止出现在管理读取模型或日志投影中：`password`、`password_hash`、`mfa_secret`、`mfa_private_key`、`session_hash`、`code_hash_sha256`。会话列表仅返回会话 ID、邮箱、作用域、创建/过期/最后活动时间和状态。

## 实现位置

真实适配器位于 `matharc/v02/admin_server.py`，领域服务位于 `matharc/v02/admin_service.py`，迁移命令位于 `matharc/v02/admin_migrate.py`。契约测试仍使用 fake 连接，并不声明 PostgreSQL 已在生产部署或人工验收已完成。
