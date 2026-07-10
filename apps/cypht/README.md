## 使用说明

部署成功后，浏览器访问 `http://<服务器IP>:<端口>`，使用安装时设置的管理员用户名和密码登录。

> 安装前需先在 1Panel 应用商店安装 PostgreSQL 和 Redis，安装 Cypht 时选择绑定的数据库与缓存实例并填入密码。

登录后进入 **设置 > 账户**，添加你的邮箱账户（支持 IMAP/SMTP、JMAP、EWS、Gmail、Outlook 等），Cypht 会将所有账户的邮件聚合到统一收件箱中。

> 默认语言已设为中文，时区与安装时一致。

## Outlook OAuth 配置

如需通过 OAuth 方式添加 Outlook.com 账户，需先在 Azure 门户注册应用：

1. 访问 [Azure 门户](https://portal.azure.com) → 应用注册 → 新建注册
2. **受支持的帐户类型**：选择「个人 Microsoft 帐户」（Personal Microsoft accounts）
3. **重定向 URI**：填 `http://你的域名:端口`（**不带查询字符串**，如 `http://mail.example.com:6020`）
4. 注册后获取 **Application (client) ID**（即 Client ID）
5. 左侧菜单 → 证书和密码 → 新建客户端密码 → 复制 **Client Secret 值**
6. **API 权限**：Cypht 使用 `wl.imap` scope（Live Connect 内置），无需在 Azure 手动添加 API 权限
7. 安装 Cypht 时在表单中填入 Client ID、Client Secret 和回调地址

> 多个 Outlook 账户可共用同一组 Client ID 和 Secret，无需每账户单独注册。
> 不配置 OAuth 也可通过 IMAP 方式添加 Outlook 账户（服务器 `outlook.office365.com:993`，TLS）。

## Gmail OAuth 配置

如需通过 OAuth 方式添加 Gmail 账户，需先在 Google Cloud Console 注册应用：

1. 访问 [Google Cloud Console](https://console.cloud.google.com) → API 和服务 → 凭据 → 创建 OAuth 客户端 ID
2. **授权重定向 URI**：填 `http://你的域名:端口/?page=home`（Gmail 允许查询字符串）
3. 启用 Gmail API
4. 获取 **Client ID** 和 **Client Secret**
5. 安装 Cypht 时在表单中填入

> 不配置 OAuth 也可通过 IMAP 方式添加 Gmail 账户（服务器 `imap.gmail.com:993`，TLS，需使用应用专用密码）。

## 产品介绍

**Cypht** 是一个轻量级开源 Web 邮件聚合客户端，使用 PHP 编写。它不替代你现有的邮箱账户，而是将多个账户（IMAP/SMTP、JMAP、EWS）和 RSS 源聚合到一个统一的界面中。

## 主要功能

- 统一收件箱：跨所有账户的收件箱、未读、已发送、星标视图
- 多账户管理：支持 IMAP/SMTP、JMAP、EWS（Exchange Web Services）
- 模块系统：灵活的插件架构，可扩展功能而无需修改核心代码
- 服务端过滤：支持 Sieve 邮件过滤，离线时也可工作
- 灵活认证：支持 IMAP、LDAP、数据库及主流邮箱提供商自动发现
- 通用搜索：跨所有邮箱账户和 RSS 源的即时搜索
- 附件管理、联系人、标签、日历等模块

> 更多细节请参见 [官方文档](https://www.cypht.org/documentation)。