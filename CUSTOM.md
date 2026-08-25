# appstore

1panel 私有应用商店 — 自托管应用集合，涵盖代理、监控、邮件、笔记、AI 等工具。

## 构建 / 发布

面板（1Panel v1 协议）不直接读取 `apps/` 目录，而是拉取 `dev/` 下的协议产物与 Release 里的版本包：

```
apps/<key>/…   ──python3 tools/build.py──▶   dev/                     dist/
（人维护的源）      （CI 自动执行）             ├─ 1panel.json.version.txt    ├─ <key>-<ver>.tar.gz
                                              ├─ 1panel.json.zip            （上传到 packages Release）
                                              └─ 1panel/<key>/<ver>/…
```

- **日常发布**：改 `apps/` 后 push 到 main 即可，Actions 自动构建、回推 `dev/`、上传 Release（`.github/workflows/publish.yml`）
- **本地构建**：`pip install pyyaml && python3 tools/build.py`，产物在 `dev/` 与 `dist/`
- **手动发布**（CI 故障兜底）：
  ```bash
  python3 tools/build.py
  git add dev/ && git commit -m "build: regenerate dev/ [skip ci]" && git push
  gh release create packages --title "App Packages" --notes "auto" || true
  gh release upload packages dist/*.tar.gz --clobber
  ```

约定与注意事项：

- 版本目录名即面板显示版本号；**纯数字分段**（如 `3.6.1`）才能正常提示升级，`latest` 可以安装但永不提示更新
- 每个版本目录必须有 `docker-compose.yml`；应用根目录必须有 `logo.png` 与 `data.yml`
- 配置模板用 `__占位符__` + `scripts/init.sh` 注入，勿提交真实密钥
- 面板侧指向本仓库：`app_repo: https://raw.githubusercontent.com/lanqiguoguo/appstore`（mode 保持 dev）

## 应用列表

| 应用 | 说明 |
|------|------|
| 3xui | 3X-UI — Xray-core 服务器管理面板 |
| als | ALS — 网络诊断 Looking-glass 服务 |
| bifrost | Bifrost AI 网关 — 高性能 AI API 网关，支持自动故障转移、负载均衡与语义缓存 |
| ccx | AI API 代理与协议转换网关，支持 Claude、OpenAI、Gemini 等 |
| cpa | CLIProxyAPI — AI 网关代理，为 CLI 提供多模型兼容 API 与内置 Web UI |
| cpamp | CPA Manager Plus — AI 网关监控面板，追踪请求、成本、配额与账号健康 |
| fast_note_sync | Fast Note Sync Service — Obsidian 高性能笔记同步、管理与 REST API 服务 |
| ghproxy | GitHub 资源代理，支持 Docker 镜像加速 |
| hubproxy | 多功能代理服务，支持 Docker 镜像 / GitHub 文件加速 |
| komari | 轻量级自托管服务器监控工具 |
| litellm | Python SDK 与代理服务器（AI 网关），以 OpenAI 格式调用 100+ LLM API，提供成本追踪、护栏、负载均衡与日志记录 |
| mailflow | 自托管统一 Web 邮件客户端，支持多 IMAP 账户 |
| miaomiaowu | 妙妙屋 — 个人 Clash 订阅管理系统 |
| miaomiaowux | 妙妙屋X — 增强版，支持远程服务器管理、Xray 服务管理、证书管理 |
| microbin | 微型自托管 Paste Bin 服务 |
| obsidian_livesync | Obsidian LiveSync — 自托管 CouchDB 双向同步 |
| open-notebook | 私有本地 AI Notebook，支持 18+ AI 提供商、多模态内容 |
| outlookemail | 多邮箱管理工具，支持 Outlook/Gmail/QQ/163 等 |
| renewlet | 订阅记账工具，到期前自动提醒 |
| searxng | 无追踪元搜索引擎 |
| xui | 3X-UI — Xray-core 高级管理面板 |

## 更新记录

- 2026年8月8日
  - 新增 cpa（CLIProxyAPI，latest）

- 2026年7月31日
  - 新增 bifrost

- 2026年7月24日
  - 更新 fast_note_sync 3.6.0
  - 更新 mailflow 2.7.0
- 2026年7月15日
  - 更新 cli_proxy_api v7.2.77
- 2026年7月14日
  - 更新 xui v3.5.0
  - 更新 mailflow 2.5.0
  - 更新 cli_proxy_api v7.2.74
- 2026年7月13日
  - 更新 cli_proxy_api v7.2.72
  - 更新 cli_proxy_api v7.2.71
- 2026年7月12日
  - 新增 cli_proxy_api
  - 新增 cpa_manager_plus
  - ~~cypht~~
- 2026年7月10日
  - ~~新增 cypht~~
- 2026年7月8日
  - 更新 mailflow 2.3.0
- 2026年7月5日
  - 更新 xui v3.4.2
  - 更新 fast_note_sync 3.5.1
  - 更新 mailflow 2.0.2
  - ~~portkey~~
- 2026年6月29日
  - ~~新增 portkey~~
- 2026年6月28日
  - 新增 fast_note_sync
  - 更新 xui v3.4.1
  - 更新 mailflow 1.7.3
  - 更新 miaomiaowu 0.8.2
  - 新增 litellm
  - 更新 mailflow 1.7.0
  - 更新 renewlet
- 2025年6月19日
  - 更新 mailflow 1.6.0
  - 更新 open-notebook v1-latest
- 2025年10月3日
  - ~~s-ui~~
- 2025年9月18日
  - als
  - komari
- 2025年9月17日
  - obsidian_livesync
  - microbin
  - hubproxy
  - ~~Wallos~~
  - 3xui
