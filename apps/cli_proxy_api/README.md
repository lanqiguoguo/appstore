## 使用说明

部署成功后，浏览器访问 `http://<服务器IP>:<端口>/management.html`，使用安装时设置的管理密钥登录 Web UI。

在 Web UI 中可以配置 AI 提供商、认证文件、API 密钥、路由策略等。

## OAuth 登录

如需使用 OAuth 方式接入提供商（Codex、Claude、Antigravity），在容器中执行登录命令：

**OpenAI Codex**：
```bash
docker exec -it <容器名> /CLIProxyAPI/CLIProxyAPI -no-browser --codex-login
```

**Claude Code**：
```bash
docker exec -it <容器名> /CLIProxyAPI/CLIProxyAPI -no-browser --claude-login
```

**Antigravity**：
```bash
docker exec -it <容器名> /CLIProxyAPI/CLIProxyAPI -no-browser --antigravity-login
```

命令会输出一个 URL，在浏览器中打开完成授权。

## 客户端接入

配置好提供商和 API 密钥后，客户端通过以下地址接入：

```
http://<服务器IP>:<端口>/v1/...
```

使用在 Web UI 中生成的 API 密钥进行认证。

## 与 cpa_manager_plus 的区别

| | cli_proxy_api | cpa_manager_plus |
|---|---|---|
| 部署形态 | 单容器（仅 CLIProxyAPI） | 双容器（CLIProxyAPI + CPAMP 监控面板） |
| 管理界面 | CLIProxyAPI 内置 Web UI | CPAMP 独立管理面板（请求监控、用量分析、账号巡检） |
| 适合场景 | 轻量部署，基础管理即可 | 需要完整的请求监控与用量分析 |

## 产品介绍

**CLIProxyAPI** 是一个为 CLI 工具提供 OpenAI/Gemini/Claude/Codex/Grok 兼容 API 的代理服务器。支持多账户轮询、负载均衡、OAuth 登录，内置 Web UI 管理面板。

## 主要功能

- OpenAI/Gemini/Claude/Codex/Grok 兼容 API 端点
- 多账户支持与轮询负载均衡
- 内置 Web UI 管理面板（`/management.html`）
- OAuth 登录（Codex、Claude、Antigravity）
- OpenAI 兼容提供商接入（如 OpenRouter）
- 流式与非流式响应、函数调用、多模态输入
- 配额管理与自动切换
- 插件系统
- 日志写入文件（默认 10MB 滚动）

## 数据持久化

| 目录 | 说明 |
|------|------|
| `./config/` | 配置文件（安装时由 init.sh 注入管理密钥） |
| `./auths/` | 认证文件（OAuth 凭证、API 密钥） |
| `./logs/` | 日志文件 |
| `./plugins/` | 插件目录 |

> 更多细节请参见 [官方文档](https://help.router-for.me/cn/configuration/basic.html)。