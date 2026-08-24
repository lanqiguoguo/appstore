# OpenResty

OpenResty（基于 NGINX 与 LuaJIT）是一个高性能 Web 平台，可以轻松搭建动态 Web 应用、Web 服务和动态网关，支持 Lua 脚本扩展。

- 官方文档: https://openresty.org/en/getting-started.html
- 项目主页: https://github.com/openresty/openresty

## 使用说明

安装后应用目录结构如下：

```
├── conf/
│   ├── nginx.conf      # 主配置（可编辑）
│   └── conf.d/         # 站点配置目录（*.conf 会被自动加载）
├── html/               # 网站根目录（默认首页在此）
└── log/                # 访问日志与错误日志
```

- 默认通过安装时填写的「应用端口」访问
- 修改 `conf/nginx.conf` 或 `conf/conf.d/` 下的配置后，重启应用生效
- 网站文件放入 `html/` 目录即可直接访问

## Configuration

- Web root: `./html` → `/usr/local/openresty/nginx/html`
- Main config: `./conf/nginx.conf`
- Site configs: `./conf/conf.d/*.conf` (auto-included)
- Logs: `./log`
