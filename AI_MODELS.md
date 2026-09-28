# 明鉴可选大模型调研与接口说明

更新日期：2026-09-28

## 产品原则

明鉴的内置规则、PDF/DOCX/XLSX解析和报告导出全部随EXE提供。普通用户不需要注册账号、安装模型、填写API Key或启动服务。添加或拖入材料后，程序自动开始审查。

大模型接口属于可选增强。用户启用后，模型用于补充语义一致性、表达歧义和潜在风险检查；内置规则仍会执行，模型结论统一标记为“大模型”，并要求人工复核。

## 推荐免费模型

| 模型 | 许可证 | 典型本地体积 | 适用建议 |
|---|---|---:|---|
| Qwen3.5 4B | Apache 2.0 | Ollama量化版约3.4 GB | 默认推荐，中文能力和普通电脑资源占用较平衡 |
| Qwen3.5 9B | Apache 2.0 | Ollama量化版约6.6 GB | 适合16 GB以上内存，语义审查更稳定 |
| DeepSeek-R1 Distill Qwen 7B | MIT，基础Qwen采用Apache 2.0 | Ollama量化版约4.7 GB | 适合复杂条款推理，输出速度相对较慢 |

参考：

- Qwen3.5 4B：https://huggingface.co/Qwen/Qwen3.5-4B
- Qwen3.5 9B：https://huggingface.co/Qwen/Qwen3.5-9B
- Ollama Qwen3.5：https://ollama.com/library/qwen3.5
- DeepSeek-R1 Distill Qwen 7B：https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B

## 已实现接口

桌面端“模型接口”支持两类服务：

1. OpenAI兼容接口：`GET /models`、`POST /chat/completions`；
2. Ollama本地接口：`GET /api/tags`、`POST /api/chat`。

配置项包括接口类型、基础地址、模型名称和API Key。API Key保存在当前Windows用户的Qt配置中，不写入项目文件和审查报告。

## 输出协议

模型必须返回JSON：

```json
{
  "findings": [
    {
      "severity": "blocking|high|medium|info",
      "title": "问题标题",
      "detail": "问题说明",
      "file": "准确文件名",
      "page": 1,
      "excerpt": "原文证据",
      "suggestion": "整改建议"
    }
  ]
}
```

程序会限制返回数量和字段长度，并在接口不可用、超时或返回格式错误时保留内置规则结果。
