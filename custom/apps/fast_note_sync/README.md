## 使用说明

部署成功后，浏览器访问 `http://<服务器IP>:<端口>` 进入管理面板。

1. **初始化账号**：首次访问需注册一个账号（如需关闭公开注册，可在管理面板内停用或自定义 [config.yaml](https://github.com/haierkeys/fast-note-sync-service/blob/master/config/config.yaml) 后挂入容器）。
2. **获取配置**：登录后点击右上角 **"复制 API 配置"**。
3. **连接 Obsidian**：打开 [Obsidian Fast Note Sync 插件](https://github.com/haierkeys/obsidian-fast-note-sync) 的设置页，粘贴刚才复制的配置即可开始同步。

> 数据持久化目录：`storage/`（数据库、附件、日志）和 `config/`（首次启动自动生成默认 `config.yaml`，可按需编辑覆盖）。请在 1Panel 中注意备份这两个目录。

## 产品介绍

**Fast Note Sync Service (FNS)** 是基于 Golang + WebSocket + React 实现的高性能、低延迟 Obsidian 笔记同步服务，多设备毫秒级实时同步，自带 Web 管理面板与 REST API。

## 主要功能

- 多设备实时双向同步（毫秒级）与附件/图片同步（支持分块上下传）
- 内置 Web 管理面板：创建用户、生成插件配置、管理 Vault 与笔记
- 标准 REST API，支持脚本化与 AI 助手集成
- 原生 MCP（Model Context Protocol）支持，可接入 Cherry Studio / Cursor / Claude Code
- 笔记历史版本、回收站、离线编辑自动合并、文件夹同步
- 笔记分享（带密码、短链、访问统计）
- Git 自动化托管与多存储备份（S3 / OSS / R2 / WebDAV / 本地）
- 多数据库支持：SQLite（默认零依赖）/ MySQL / PostgreSQL

> 更多细节请参见 [官方文档](https://github.com/haierkeys/fast-note-sync-service)。