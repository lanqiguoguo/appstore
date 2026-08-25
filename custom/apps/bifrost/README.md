Bifrost AI 网关 — 高性能 AI API 网关

Bifrost 是一个高性能 AI 网关，通过统一的 OpenAI 兼容 API 接入 23+ 提供商（OpenAI、Anthropic、AWS Bedrock、Google Vertex、Azure、Cerebras、Cohere、Mistral、Ollama、Groq 等），支持自动故障转移、负载均衡、语义缓存、MCP 工具与企业级治理功能。

### 特性
- **统一接口** — 单一 OpenAI 兼容 API 接入所有提供商
- **自动故障转移** — 提供商与模型间无缝切换，零停机
- **负载均衡** — 跨多个 API Key 和提供商的智能请求分发
- **语义缓存** — 基于语义相似度的智能响应缓存，降低成本和延迟
- **Web UI** — 内置可视化配置界面与实时监控
- **MCP 支持** — 让 AI 模型使用外部工具（文件系统、Web 搜索、数据库）
- **多模态** — 支持文本、图像、音频与流式传输
- **治理与安全** — 用量跟踪、速率限制、虚拟密钥与访问控制
- **可观测性** — 原生 Prometheus 指标、分布式追踪与日志

### 快速开始

```bash
# Docker
docker run -p 8080:8080 maximhq/bifrost

# 或使用 npx
npx -y @maximhq/bifrost

# 打开 Web UI
open http://localhost:8080
```
