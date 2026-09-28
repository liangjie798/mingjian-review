# 明鉴开发文档

## 1. 当前版本

- 版本：0.2.0 MVP
- 平台：Windows 10/11 x64
- 桌面框架：PyWebView + 本地FastAPI服务
- 前端：React 19 + TypeScript + Vite
- 后端：Python 3.13 + FastAPI + Pydantic
- 打包：PyInstaller单文件模式
- 当前产物：`dist/MingJian.exe`

当前版本完整展示竞赛材料审查和合同审查两个工作台，支持上传PDF、DOCX、XLSX、TXT、MD、CSV和JSON。原生PDF由PyMuPDF解析，Word由python-docx解析，Excel由openpyxl解析。

## 2. 设计来源与原创边界

项目参考了以下GitHub开源项目的能力划分：

| 项目 | 参考内容 | 本项目实现 |
|---|---|---|
| PaddleOCR / PP-StructureV3 | OCR、版面与表格解析 | 预留扫描件解析适配器，MVP尚未打包模型 |
| Docling / MinerU | 统一文档对象、页块定位 | 自定义轻量页面文本模型 |
| Instructor + Pydantic | 结构化输出和Schema校验 | Pydantic定义Evidence、Finding和接口响应 |
| doc_assistant | 证据与解释分离 | 每条问题关联文件、页码和原文 |
| Ethos | 确定性证据验证 | 审查结果必须携带Evidence对象 |
| OfficeComprehensionBench | 文档能力评测 | 采用字段、问题和证据分别评价的思路 |

本项目没有复制完整开源应用。场景包、竞赛规则、合同规则、事实对照、整改状态和前端交互均由本项目独立实现。

## 3. 系统架构

```text
PyWebView桌面窗口
        │
        ▼
React静态页面
        │ HTTP / multipart
        ▼
FastAPI本地服务
        ├── 文件格式路由
        ├── PDF / Word / Excel解析
        ├── 竞赛规则执行器
        ├── 合同规则执行器
        └── Evidence / Finding结构化响应
```

桌面程序只监听`127.0.0.1`。默认端口为8765，端口被占用时自动选择空闲端口。

## 4. 目录结构

```text
.
├── src/                       React界面
│   ├── App.tsx                场景首页、工作台和文件上传
│   ├── data.ts                内置演示数据
│   ├── types.ts               前端类型
│   └── styles.css             视觉系统和响应式布局
├── backend/
│   ├── app.py                 API、解析器和规则执行器
│   └── requirements.txt       固定Python依赖
├── scenario-packs/
│   ├── competition/           竞赛场景配置
│   └── contract/              合同场景配置
├── desktop.py                 桌面窗口与本地服务启动器
├── mingjian.spec              PyInstaller构建配置
├── build.ps1                  一键构建脚本
├── DEV_STEPS.md               后续开发路线
├── DEVELOPMENT.md             本开发文档
└── 材料审查智能体项目资料.md    调研、产品和评测资料
```

## 5. 本地开发

### 环境要求

- Node.js 22或兼容版本；
- Python 3.13；
- Windows WebView2 Runtime。Windows 10/11通常已安装。

### 前端开发

```powershell
npm install
npm run dev
```

### 后端开发

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload
```

前端开发地址为`http://localhost:5173`，后端文档为`http://127.0.0.1:8000/docs`。

### 生产模式源码运行

```powershell
npm run build
.\.venv\Scripts\python.exe desktop.py
```

## 6. API

### 健康检查

```http
GET /api/health
```

### 场景列表

```http
GET /api/scenarios
```

### 内置演示审查

```http
POST /api/demo/review
Content-Type: application/json

{"scenario":"competition"}
```

### 上传文件审查

```http
POST /api/review/files
Content-Type: multipart/form-data

scenario=competition|contract
files=<一个或多个文件>
```

响应包括每个文件的解析器、页数、字符数和审查问题列表。

## 7. 当前规则

### 竞赛审查

- 按文件名检查报名表、项目书和承诺书；
- 从“团队成员”字段估算人数；
- 问题输出风险等级、证据和整改建议；
- 无确定问题时进入人工复核状态。

### 合同审查

- 识别预付款比例，演示规则上限为30%；
- 检查是否提及验收但没有明确验收期限；
- 无确定问题时提示继续人工检查主体、金额和责任条款。

这些是可演示的确定性规则，不构成赛事资格认定或法律意见。

## 8. 新增场景

1. 在`scenario-packs/<场景名>/`增加`manifest.json`和`default-rules.json`。
2. 在后端增加场景审查函数，输入统一为`list[tuple[str, list[str]]]`。
3. 输出统一使用`Finding`，且至少包含一条`Evidence`。
4. 在`src/data.ts`注册场景卡片。
5. 增加一个正确样本和至少三个错误样本。

后续应将当前Python函数式规则迁移为通用操作符，例如`required_document`、`regex_extract`、`between`、`equals_across_documents`和`sum_equals`。

## 9. EXE构建

执行：

```powershell
.\build.ps1
```

脚本会：

1. 使用`npm ci`恢复前端依赖；
2. 执行TypeScript检查和Vite生产构建；
3. 创建`.venv`并安装固定Python依赖；
4. 使用`mingjian.spec`生成单文件EXE；
5. 计算SHA-256并写入校验文件。

PyInstaller配置只嵌入`dist/index.html`、`dist/assets`和`scenario-packs`，避免将旧EXE再次嵌入新EXE。

## 10. 验证

构建后可用服务模式验证，不打开桌面窗口：

```powershell
.\dist\MingJian.exe --server-only --port 8877
```

另一个终端执行：

```powershell
Invoke-RestMethod http://127.0.0.1:8877/api/health
```

本次构建已验证：

- 前端生产构建通过；
- EXE健康接口返回`ok`；
- EXE内嵌首页返回HTTP 200；
- multipart文件上传成功；
- 竞赛和合同规则均返回结构化Finding。

## 11. 已知限制

- 当前PDF解析只支持带文字层的原生PDF；扫描PDF需要后续接入PaddleOCR。
- 当前没有接入大模型，规则抽取和语义审查使用内置演示逻辑。
- DOC旧格式、XLS旧格式和图片尚未支持。
- 页面预览是证据模拟视图，尚未根据PDF坐标绘制真实高亮框。
- EXE未进行代码签名，Windows可能显示未知发布者提示。
- 未实现项目持久化、版本管理和PDF报告导出。

## 12. 下一阶段

1. 接入PaddleOCR PP-StructureV3，补充扫描PDF和图片解析。
2. 将场景JSON转换为通用规则执行器。
3. 增加跨文档事实表和名称规范化。
4. 增加规则确认工作台，避免AI自动执行未经确认的规则。
5. 制作30组测试材料并统计精确率、召回率和证据定位准确率。
6. 增加安装包、应用图标、代码签名和GitHub Releases自动发布。

## 13. 产品官网与下载发布

官网位于`website/`，使用原生HTML、CSS和JavaScript构建，无运行时依赖。首页包含产品定位、真实软件截图、审查能力、工作流程、本地处理说明和Windows下载入口；`development.html`提供面向参赛评委与开发者的技术说明。

本地预览：

```powershell
npx vite website --host 127.0.0.1 --port 4175
```

重新构建桌面端后，需要同步下载文件并更新校验值：

```powershell
Copy-Item .\dist\MingJian.exe .\website\downloads\MingJian.exe -Force
Copy-Item .\dist\MingJian.exe.sha256.txt .\website\downloads\MingJian.exe.sha256.txt -Force
```

`.github/workflows/deploy-pages.yml`会在`main`分支更新时部署`website/`。当前官网直接托管EXE；正式发布时可把下载链接改为GitHub Releases，以保留历史版本和发布说明。
