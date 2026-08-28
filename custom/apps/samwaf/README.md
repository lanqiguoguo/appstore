SamWaf 是一款开源轻量级的 Web 应用防火墙，面向小型团队与家庭实验室，基于反向代理为站点提供防护。

[源码](https://github.com/samwafgo/SamWaf) | [使用文档](https://github.com/samwafgo/SamWaf/wiki)

## 特性

- 反向代理接入，支持 HTTP/HTTPS 站点防护
- IP 黑白名单、地域封禁（支持 iptables 封禁）
- CC 攻击防御、自定义防护规则
- TLS 证书管理与自动续期（ACME）
- 内置日志与攻击分析

## 端口说明

| 端口 | 用途 |
| --- | --- |
| 26666 | 管理面板（首次访问初始化管理员账号） |
| 80 / 443 | 站点反代端口，按需在安装时修改以避免端口冲突 |

> [!NOTE]
> 容器需要 `NET_ADMIN` 权限以支持基于 iptables 的 IP 封禁功能。

本应用使用 [samwaf-docker](https://github.com/lanqiguoguo/samwaf-docker) 构建的多架构精简镜像（amd64/arm64）。
