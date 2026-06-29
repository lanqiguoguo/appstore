## 使用说明

部署成功后，通过 `http://<服务器IP>:<端口>` 即可访问 AI Gateway API。

### 快速验证

```bash
curl http://localhost:6019/v1/chat/completions \
  -H "Authorization: Bearer OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

将请求中的 `localhost:6019` 替换为你的实际地址，`OPENAI_API_KEY` 替换为目标 LLM 提供商的密钥即可。

## 产品介绍

**Portkey AI Gateway** 是一个开源、轻量、企业级的 AI 网关，可路由至 1600+ 语言、视觉、音频和图像模型，延迟低于 1ms，体积仅 122KB。

## 主要功能

- 统一 API 路由至 1600+ LLM（OpenAI、Anthropic、Google、Azure 等）
- 50+ AI 护栏（Guardrails）
- 负载均衡、重试、回退、超时控制
- 请求缓存与速率限制
- 日志记录与分析

> 更多细节请参见 [官方文档](https://github.com/Portkey-AI/gateway)。