一个基于Go的高性能Github资源代理程序, 同时支持Docker镜像代理与脚本嵌套加速等多种功能
项目说明
项目特点

    ⚡ 基于 Go 语言实现，跨平台的同时提供高并发性能
    🌐 使用自有Touka框架作为 HTTP服务端框架
    📡 使用 Touka-HTTPC 作为 HTTP 客户端
    📥 支持 Git clone、raw、releases 等文件拉取
    🐳 支持反代Docker, GHCR等镜像仓库
    🎨 支持多个前端主题
    🚫 支持自定义黑名单/白名单
    🗄️ 支持 Git Clone 缓存（配合 Smart-Git）
    🐳 支持自托管与Docker容器化部署
    ⚡ 支持速率限制
    ⚡ 支持带宽速率限制
    🔒 支持用户鉴权
    🐚 支持 shell 脚本多层嵌套加速

项目相关

[DEMO](https://ghproxy.1888866.xyz/)