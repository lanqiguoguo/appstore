## 使用说明

部署包含两个服务：**CPA 网关运行时**（API 端口）和 **CPAMP 管理面板**（面板端口）。

### 1. 获取管理员密钥

如果安装时填写了 CPAMP 管理员密钥，直接使用该密钥。如果留空，CPAMP 会自动生成，通过以下命令查看启动日志获取：

```bash
docker compose logs cpa-manager-plus
```

日志中会输出一次 `cpamp_...` 格式的管理员密钥。

### 2. 首次配置

浏览器访问 `http://<服务器IP>:<面板端口>/management.html`，按顺序填写：

1. **CPAMP 管理员密钥**：上一步获取的密钥
2. **CPA 地址**：`http://cli-proxy-api:8317`（Docker 内网服务名）
3. **CPA Management Key**：安装时填写的 CPA Management Key
4. **请求监控采集方式**：保持默认 `auto` 即可

### 3. 三种密钥说明

| 密钥 | 用途 | 来源 |
|------|------|------|
| CPAMP 管理员密钥 | 登录 CPAMP 管理面板 | 安装时填写或自动生成 |
| CPA Management Key | CPAMP 连接 CPA 的远程管理密钥 | 安装时填写，已注入 CPA config.yaml |
| CPA API 密钥 | 客户端请求模型 API 时使用 | 部署后在 CPAMP 面板中配置 |

### 4. 配置 CPA 提供商和 API 密钥

完成首次 setup 后，在 CPAMP 面板中配置：
- **AI 提供商**：设置 > AI 提供商，添加 OpenAI、Anthropic、Gemini 等
- **认证文件**：设置 > 认证文件，上传 OAuth 凭证
- **API 密钥**：设置 > 配置中心，生成供客户端使用的 API 密钥
- **配额管理**：设置 > 配额管理，设置账号配额限制

客户端使用 API 密钥通过 `http://<服务器IP>:<API端口>/v1/...` 调用模型。

## 产品介绍

**CPA Manager Plus (CPAMP)** 是自托管 AI 网关监控面板，配合 CPA (CLI Proxy API) 使用。CPA 处理模型请求转发，CPAMP 负责监控、分析和管理。

## 主要功能

- 仪表盘：Manager Server / CPA 连接状态总览
- 请求监控：实时请求记录与详情
- 用量分析：按模型、账号、项目、时间范围拆解成本与 Token
- Codex 账号巡检：配额、重置时间、凭证状态和账号健康
- 配额管理：账号配额限制与告警
- 模型价格：成本估算与价格同步
- 插件管理：支持从 GitHub Release 安装插件
- OAuth 登录：支持多提供商 OAuth 认证
- 认证文件管理：上传与管理凭证文件

## 1Panel OpenResty 反向代理配置

如需通过同一域名访问面板和 API，在 1Panel 中为该应用创建 OpenResty 反向代理，使用以下路径分流规则：

```
浏览器
  -> https://your-domain.com
      -> /management.html           -> CPAMP :18317（面板端口）
      -> /usage-service/*           -> CPAMP :18317
      -> /v0/management/*           -> CPAMP :18317
      -> /v0/resource/plugins/*     -> CPAMP :18317
      -> /v1/*, /v1beta/*           -> CPA :8317（API 端口）
      -> /backend-api/codex/*       -> CPA :8317
      -> /anthropic/callback        -> CPA :8317
      -> /codex/callback            -> CPA :8317
      -> / (兜底)                   -> CPA :8317
```

在 1Panel 的网站设置中，编辑 Nginx 配置，添加以下内容：

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

upstream cpa_api {
    server 127.0.0.1:60211;
}

upstream cpamp {
    server 127.0.0.1:6021;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 64m;

    proxy_http_version 1.1;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    proxy_buffering off;

    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade           $http_upgrade;
    proxy_set_header Connection        $connection_upgrade;

    location = / {
        return 302 /management.html;
    }

    # ===== CPAMP 面板 =====
    location = /management.html { proxy_pass http://cpamp; }
    location = /health          { proxy_pass http://cpamp; }
    location = /status          { proxy_pass http://cpamp; }
    location = /setup           { proxy_pass http://cpamp; }
    location ^~ /usage-service/ { proxy_pass http://cpamp; }
    location ^~ /v0/management/ { proxy_pass http://cpamp; }
    location ^~ /v0/resource/plugins/ { proxy_pass http://cpamp; }
    location = /models          { proxy_pass http://cpamp; }

    # ===== CPA API =====
    location ^~ /v1/                 { proxy_pass http://cpa_api; }
    location ^~ /v1beta/             { proxy_pass http://cpa_api; }
    location ^~ /backend-api/codex/  { proxy_pass http://cpa_api; }
    location ^~ /api/                { proxy_pass http://cpa_api; }
    location = /v1internal:method    { proxy_pass http://cpa_api; }
    location = /healthz              { proxy_pass http://cpa_api; }
    location = /anthropic/callback   { proxy_pass http://cpa_api; }
    location = /codex/callback       { proxy_pass http://cpa_api; }
    location = /google/callback      { proxy_pass http://cpa_api; }
    location = /antigravity/callback { proxy_pass http://cpa_api; }

    # 兜底给 CPA
    location / {
        proxy_pass http://cpa_api;
    }
}
```

> HTTPS 只需调整 `listen` 和证书配置，location 分流规则不变。
> 上游端口 `6021` 和 `60211` 需替换为实际安装时使用的端口。

## 数据持久化与备份

必须备份以下目录：

| 目录 | 说明 |
|------|------|
| `./data/` | CPAMP SQLite 数据库和加密密钥（`usage.sqlite`、`data.key`） |
| `./config/` | CPA 配置模板（首次启动时注入 Management Key 生成实际配置） |
| `./cpa-data/` | CPA 运行数据和实际配置文件（`config.yaml` 首次启动后生成于此） |
| `./cpa-auths/` | CPA 认证文件 |
| `./cpa-logs/` | CPA 日志 |

`data.key` 非常重要：丢失后保存到 SQLite 的 CPA Management Key 无法恢复。

> 更多细节请参见 [官方文档](https://seakee.github.io/CPA-Manager-Plus/docs/guide/getting-started.html)。