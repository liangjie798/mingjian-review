# 明鉴

多场景材料智能审查与证据溯源平台。当前MVP包含大学生竞赛审查、合同审查和科研材料审查预览，并已生成Windows桌面版。

## 当前能力

- 多场景入口与工作台；
- 竞赛材料和合同审查演示数据；
- 风险分级、原文证据和整改建议；
- 问题销项及重新审查交互；
- PDF、DOCX、XLSX和文本文件本地解析；
- FastAPI上传与审查接口；
- 可插拔场景包示例。

## 直接运行

双击`dist/MingJian.exe`。程序会启动本地服务并打开桌面窗口，不需要单独安装Python或Node.js。

## 产品官网

`website/`包含可直接部署到GitHub Pages的静态官网，提供产品介绍、真实界面预览、开发说明和Windows版下载。

本地预览：

```powershell
npx vite website
```

推送到GitHub的`main`分支后，`.github/workflows/deploy-pages.yml`会发布`website/`。仓库需要在Settings > Pages中选择GitHub Actions作为发布来源。

## 本地运行

前端：

```powershell
npm install
npm run dev
```

后端：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload
```

访问 `http://localhost:5173`，接口文档位于 `http://127.0.0.1:8000/docs`。

## 说明

当前已接入基础文件解析和确定性演示规则，尚未接入扫描件OCR和大模型。架构、构建及验证方式见[DEVELOPMENT.md](./DEVELOPMENT.md)，后续路线见[DEV_STEPS.md](./DEV_STEPS.md)，官网发布说明见[website/README.md](./website/README.md)。
