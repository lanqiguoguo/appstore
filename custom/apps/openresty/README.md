# OpenResty

OpenResty（基于 NGINX 与 LuaJIT）是一个高性能 Web 平台，可以轻松搭建动态 Web 应用、Web 服务和动态网关，支持 Lua 脚本扩展。

- 官方文档: https://openresty.org/en/getting-started.html
- 项目主页: https://github.com/openresty/openresty

## 使用说明

本应用结构参考 1Panel 官方商店 OpenResty（去除定制 WAF 部分），使用官方镜像 `openresty/openresty`，采用 host 网络模式，HTTP/HTTPS 端口在安装时指定（默认 80/443）。

安装后应用目录结构如下：

```
├── conf/
│   ├── nginx.conf        # 主配置（可编辑）
│   ├── fastcgi_params    # FastCGI 参数
│   ├── fastcgi-php.conf  # PHP FastCGI 配置
│   ├── mime.types        # MIME 类型
│   └── conf.d/           # 站点配置目录（*.conf 自动加载）
├── root/                 # 默认站点根目录（/usr/share/nginx/html）
├── www/                  # 站点目录（/www）
└── log/                  # 访问日志与错误日志（/var/log/nginx）
```

- 安装时填写的 HTTP/HTTPS 端口会通过 init.sh 自动写入 `conf/conf.d/` 下的配置
- 修改配置后重启应用生效
- 站点文件放入 `root/` 或 `www/` 目录

## Configuration

- Host network mode; ports set at install time (default 80/443)
- Main config: `./conf/nginx.conf`
- Site configs: `./conf/conf.d/*.conf` (auto-included)
- Web root: `./root` → `/usr/share/nginx/html`, `./www` → `/www`
- Logs: `./log` → `/var/log/nginx`
