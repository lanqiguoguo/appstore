Komari 是一款轻量级的自托管服务器监控工具，旨在提供简单、高效的服务器性能监控解决方案。它支持通过 Web 界面查看服务器状态，并通过轻量级 Agent 收集数据。

[文档](https://komari-document.pages.dev/) | [Telegram 群组](https://t.me/komari_monitor)

## 特性
- **轻量高效**：低资源占用，适合各种规模的服务器。
- **自托管**：完全掌控数据隐私，部署简单。
- **Web 界面**：直观的监控仪表盘，易于使用。

### 2. Docker 部署
1. 创建数据目录：
   ```bash
   mkdir -p ./data
   ```
2. 运行 Docker 容器：
   ```bash
   docker run -d \
     -p 25774:25774 \
     -v $(pwd)/data:/app/data \
     --name komari \
     ghcr.io/komari-monitor/komari:latest
   ```
3. 查看默认账号和密码：
   ```bash
   docker logs komari
   ```
4. 在浏览器中访问 `http://<your_server_ip>:25774`。

> [!NOTE]
> 你也可以通过环境变量 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 自定义初始用户名和密码。