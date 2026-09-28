# 明鉴

明鉴是一款 Windows 本地材料审查工具。用户双击 EXE 后，把文件拖进窗口即可开始审查，无需安装 Python、注册账户或配置模型。

## 当前能力

- 大学生竞赛材料：检查必交材料、团队信息、日期、金额和跨文件一致性。
- 合同材料：检查付款比例、验收期限、违约责任和关键条款。
- 证据追溯：结论关联文件名、页码和原文片段。
- 本地 AI：内置 Qwen2.5-0.5B-Instruct Q4_K_M，通过 llama.cpp 在 CPU 上推理。
- 自定义模型：支持 OpenAI 兼容接口和 Ollama。
- 文件格式：PDF、DOCX、XLSX、TXT、Markdown、CSV、JSON。

## 下载

在 [Releases](https://github.com/liangjie798/mingjian-review/releases/latest) 下载 `MingJian-AI.exe` 和 SHA-256 校验文件。

## 开发

开发环境、模型准备、打包与发布方法见 [DEVELOPMENT.md](DEVELOPMENT.md)。

## 目录

```text
backend/          文档解析、规则审查和模型适配
scenario-packs/   竞赛与合同规则包
assets/           桌面端图标
website/          GitHub Pages 静态官网
desktop.py        PySide6 桌面应用
mingjian.spec     PyInstaller 单文件配置
build.ps1         Windows 构建脚本
```

## 模型与许可

模型和运行时不会提交到源码仓库。发行包包含 Qwen2.5 模型与 llama.cpp，相关来源和许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

审查结果用于辅助核对，重要合同和正式申报材料仍应由专业人员最终确认。
