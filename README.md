# 明鉴

多场景材料智能审查与证据溯源平台。当前MVP包含大学生竞赛审查、合同审查和科研材料审查预览，并已生成Windows桌面版。

## 当前能力

- 多场景入口与工作台；
- 竞赛材料和合同审查演示数据；
- 风险分级、原文证据和整改建议；
- 问题销项及重新审查交互；
- PDF、DOCX、XLSX和文本文件本地解析；
- 原生Windows工作台与多线程审查；
- 文件拖入或选择后自动审查，普通用户无需配置；
- 可选OpenAI兼容接口与Ollama本地模型；
- 可插拔场景包示例。

## 直接运行

双击`dist/MingJian.exe`，选择或拖入材料后会自动审查。程序不需要单独安装Python、Node.js或大模型。高级用户可以在“模型接口”中增加自己的OpenAI兼容服务或Ollama模型。

## 产品官网

`website/`包含可直接部署到GitHub Pages的静态官网，提供产品介绍、真实界面预览、开发说明和Windows版下载。

本地预览：

```powershell
npx vite website
```

推送到GitHub的`main`分支后，`.github/workflows/deploy-pages.yml`会发布`website/`。仓库需要在Settings > Pages中选择GitHub Actions作为发布来源。

## 本地运行

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe desktop.py
```

## 说明

当前已接入文件解析、确定性规则和可选大模型接口，尚未接入扫描件OCR。架构、构建及验证方式见[DEVELOPMENT.md](./DEVELOPMENT.md)，免费模型调研见[AI_MODELS.md](./AI_MODELS.md)，后续路线见[DEV_STEPS.md](./DEV_STEPS.md)。
