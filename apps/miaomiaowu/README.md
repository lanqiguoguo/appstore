# 妙妙屋 - 个人Clash订阅管理系统

一个轻量级、易部署的Clash订阅管理系统，支持 Nezha、DStatus 和 Komari 探针获取流量信息，导入外部机场节点等功能。

## 功能特性

### 核心功能
- 📊 流量监控 - 支持探针服务器与外部订阅流量聚合统计
- 📈 历史流量 - 30 天流量使用趋势图表
- 🔗 订阅链接 - 展示通过订阅管理上传或导入和生成订阅生成的订阅
- 🔗 订阅管理 - 上传猫咪配置文件或从其他订阅url导入生成订阅
- 🎯 生成订阅 - 从导入的节点生成订阅，可视化代理组规则编辑器
- 📦 节点管理 - 导入个人节点或机场节点，支持添加、编辑、删除代理节点
- 🔧 生成订阅 - 自定义规则或使用模板快速生成订阅
- 🎨 代理分组 - 拖拽式代理节点分组配置，支持链式代理
- 👥 用户管理 - 管理员/普通用户角色区分，订阅权限管理
- 🌓 主题切换 - 支持亮色/暗色模式
- 📱 响应式设计 - 不完全适配移动端和桌面端

### 探针支持
- [Nezha](https://github.com/naiba/nezha) 面板
- [DStatus](https://github.com/DokiDoki1103/dstatus) 监控
- [Komari](https://github.com/komari-monitor/komari) 面板

### 体验[Demo](https://demo.miaomiaowu.net)
账户/密码: test / test123

### [使用帮助](https://docs.miaomiaowu.net)

## 安装部署

### 方式 1：Docker 部署（推荐）

使用 Docker 是最简单快捷的部署方式，无需配置任何依赖环境。

#### 基础部署

```bash
docker run -d \
  --user root \
  --name miaomiaowu \
  -p 8080:8080 \
  -v $(pwd)/mmw-data:/app/data \
  -v $(pwd)/subscribes:/app/subscribes \
  -v $(pwd)/rule_templates:/app/rule_templates \
  ghcr.io/iluobei/miaomiaowu:latest
```

参数说明：
- `-p 8080:8080` 将容器端口映射到宿主机，按需调整。
- `-v ./mmw-data:/app/data` 持久化数据库文件，防止容器重建时数据丢失。
- `-v ./subscribes:/app/subscribes` 订阅文件存放目录
- `-v ./rule_templates:/app/rule_templates` 规则模板存放目录
- `-e JWT_SECRET=your-secret` 可选参数，配置token密钥，建议改成随机字符串
- 其他环境变量（如 `LOG_LEVEL`）同下文“环境变量”章节，可通过 `-e` 继续添加。

更新镜像后可执行：
```bash
docker pull ghcr.io/iluobei/miaomiaowu:latest
docker stop miaomiaowu && docker rm miaomiaowu
```
然后按照上方命令重新启动服务。

#### Docker Compose 部署

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  miaomiaowu:
    image: ghcr.io/iluobei/miaomiaowu:latest
    container_name: miaomiaowu
    restart: unless-stopped
    user: root
    environment:
      - PORT=8080
      - DATABASE_PATH=/app/data/traffic.db
      - LOG_LEVEL=info

    ports:
      - "8080:8080"

    volumes:
      - ./data:/app/data
      - ./subscribes:/app/subscribes
      - ./rule_templates:/app/rule_templates

    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/"]
      interval: 30s
      timeout: 3s
      start_period: 5s
      retries: 3

```

参数说明：
- `-p 8080:8080` 将容器端口映射到宿主机，按需调整。
- `-e JWT_SECRET=your-secret` 可选参数，配置token密钥，建议改成随机字符串
- 其他环境变量（如 `LOG_LEVEL`）同下文“环境变量”章节，可通过 `-e` 继续添加。

映射目录说明:
```
volumes:     #这是挂载下面这三个目录到宿主机的，如果你不知道这三个目录是干嘛的，不需要添加
  - ./mmw-data:/app/data #持久化数据库文件，防止容器重建时数据丢失。
  - ./subscribes:/app/subscribes #订阅文件存放目录
  - ./rule_templates:/app/rule_templates #规则模板存放目录
```

启动服务：

```bash
docker-compose up -d
```

查看日志：

```bash
docker-compose logs -f
```

停止服务：

```bash
docker-compose down
```

#### 数据持久化说明

容器使用两个数据卷进行数据持久化：

- `/app/data` - 存储 SQLite 数据库文件
- `/app/subscribes` - 存储订阅配置文件
- `/app/rule_templates` - 存储规则文件模板

**重要提示**：请确保定期备份这两个目录的数据。

### 方式 2：一键安装（Linux）
#### ⚠⚠⚠ 注意：0.1.1版本修改了服务名称，无法通过脚本更新，只能重新安装
#### 先执行以下命令卸载及转移数据
旧服务卸载及备份转移
```
sudo systemctl stop traffic-info
sudo systemctl disable traffic-info
sudo rm -rf /etc/systemd/system/traffic-info.service
sudo rm -f /usr/local/bin/traffic-info
sudo cp -rf /var/lib/traffic-info/* /etc/mmw/
```
**自动安装为 systemd 服务（Debian/Ubuntu）：**
```bash
# 下载并运行安装脚本
curl -sL https://raw.githubusercontent.com/iluobei/miaomiaowu/main/install.sh | bash
```

安装完成后，服务将自动启动，访问 `http://服务器IP:8080` 即可。

**更新到最新版本：**
```bash
# systemd 服务更新
curl -sL https://raw.githubusercontent.com/iluobei/miaomiaowu/main/install.sh | sudo bash -s update
```

**卸载服务：**
```bash
# 卸载 systemd 服务（保留数据）
curl -sL https://raw.githubusercontent.com/iluobei/miaomiaowu/main/install.sh | sudo bash -s uninstall

# 卸载后如需完全清除数据，手动删除数据目录
sudo rm -rf /etc/mmw
```

**简易安装（手动运行）：**
```bash
# 一键下载安装
curl -sL https://raw.githubusercontent.com/iluobei/miaomiaowu/main/quick-install.sh | bash

# 运行服务
./mmw
```

**卸载服务：**
```bash
# 卸载 systemd 服务（保留数据）
curl -sL https://raw.githubusercontent.com/iluobei/miaomiaowu/main/quick-install.sh | sudo bash -s uninstall

# 卸载后如需完全清除数据，手动删除数据目录
sudo rm -rf ./data ./subscribes ./rule_templates
```

**更新简易安装版本：**
```bash
# 更新到最新版本
curl -sL https://raw.githubusercontent.com/iluobei/miaomiaowu/main/quick-install.sh | bash -s update
```

**Windows：**
```powershell
# 从 Releases 页面下载 mmw-windows-amd64.exe
# https://github.com/iluobei/miaomiaowu/releases

# 双击运行或在命令行中执行
.\mmw-windows-amd64.exe
```
<details>
<summary>页面截图</summary>

![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/traffic_info.png)  
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/subscribe_url.png)  
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/probe_datasource.png)  
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/subscribe_manage.png)  
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/generate_subscribe.png)  
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/custom_proxy_group.png)  
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/node_manage.png)  
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/user_manage.png)
![image](https://github.com/iluobei/miaomiaowu/blob/main/screenshots/system_settings.png)
</details>

### 技术特点
- 🚀 单二进制文件部署，无需外部依赖
- 💾 使用 SQLite 数据库，免维护
- 🔒 JWT 认证，安全可靠
- 📱 响应式设计，支持移动端

## ⚠️ 免责声明

- 本程序仅供学习交流使用，请勿用于非法用途
- 使用本程序需遵守当地法律法规
- 作者不对使用者的任何行为承担责任

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=iluobei/miaomiaowu&type=date&legend=top-left)](https://www.star-history.com/#iluobei/miaomiaowu&type=date&legend=top-left)


## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 问题反馈：[GitHub Issues](https://github.com/iluobei/miaomiaowu/issues)
- 功能建议：[GitHub Discussions](https://github.com/iluobei/miaomiaowu/discussions)