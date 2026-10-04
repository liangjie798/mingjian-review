# 明鉴

明鉴是一款使用 C# + WPF 编写的 Windows 原生材料审查工具。用户双击 EXE 后，把文件拖进窗口即可开始审查，无需安装运行环境、注册账户或配置模型。

## 当前能力

- 大学生竞赛材料：包含通用竞赛、数学建模、互联网+ / 创新大赛、挑战杯，分别检查必交材料、正文结构和跨文件一致性。
- 合同材料：检查付款比例、验收期限、违约责任和关键条款。
- 合同版本对比：并排比较甲乙双方合同，使用颜色高亮新增、删除和修改内容。
- 证据追溯：结论关联文件名、页码和原文片段。
- 本地 AI：内置 Qwen2.5-0.5B-Instruct Q4_K_M，通过 llama.cpp 在 CPU 上推理。
- 自定义模型：支持 OpenAI、Anthropic Claude、Google Gemini、DeepSeek、通义千问、智谱 GLM、Kimi、豆包、硅基流动、OpenRouter、Ollama 和其他 OpenAI 兼容服务。
- 文件格式：PDF、DOCX、XLSX、TXT、Markdown、CSV、JSON。
- 原生交互：深色/浅色主题、页面切换动效、拖放文件、风险详情与自绘窗口。
- 审查报告：把风险、证据与处理建议导出为 Markdown 文档。

## 下载

在 [Releases](https://github.com/liangjie798/mingjian-review/releases/latest) 下载 `MingJian-AI.exe` 和 SHA-256 校验文件。

## 开发

开发环境、模型准备、打包与发布方法见 [DEVELOPMENT.md](DEVELOPMENT.md)，模块设计见 [C# 桌面端架构](docs/CSHARP_ARCHITECTURE.md)。

## 目录

```text
src/MingJian.Desktop/  C# + WPF 主程序、解析、规则和模型适配
tests/                 WPF 核心功能自动化测试
docs/                  C# 架构与开发说明
scenario-packs/        竞赛与合同规则包
assets/                桌面端图标
website/               GitHub Pages 静态官网
build.ps1              WPF 单文件 EXE 构建脚本
```

## 模型与许可

模型和运行时不会提交到源码仓库。发行包包含 Qwen2.5 模型与 llama.cpp，相关来源和许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

审查结果用于辅助核对，重要合同和正式申报材料仍应由专业人员最终确认。
