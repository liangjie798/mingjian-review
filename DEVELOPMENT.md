# 明鉴开发文档

## 1. 当前版本

- 版本：0.3.0 Native Desktop
- 平台：Windows 10/11 x64
- 桌面框架：CustomTkinter原生窗口
- 审查引擎：Python 3.13纯本地模块
- 官网：独立HTML、CSS和JavaScript静态站点
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
CustomTkinter原生工作台
        │ Python函数调用
        ▼
本地审查引擎
        ├── 文件格式路由
        ├── PDF / Word / Excel解析
        ├── 竞赛规则执行器
        ├── 合同规则执行器
        └── Evidence / Finding结构化结果
```

桌面程序不启动HTTP服务、不打开WebView，也不监听本地端口。界面线程只负责交互，文件解析和规则执行放在后台线程，避免审查大文件时阻塞窗口。

## 4. 目录结构

```text
.
├── backend/
│   ├── review_engine.py       文件解析、规则与统一结果模型
│   └── app.py                 保留的开发期API适配层
├── scenario-packs/
│   ├── competition/           竞赛场景配置
│   └── contract/              合同场景配置
├── assets/                    应用图标
├── desktop.py                 原生桌面工作台
├── requirements-desktop.txt  桌面构建依赖
├── mingjian.spec              PyInstaller构建配置
├── build.ps1                  一键构建脚本
├── DEV_STEPS.md               后续开发路线
├── DEVELOPMENT.md             本开发文档
└── 材料审查智能体项目资料.md    调研、产品和评测资料
```

## 5. 本地开发

### 环境要求

- Python 3.13；
- Windows 10或Windows 11。

### 桌面端开发

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe desktop.py
```

## 6. 可选开发API

`backend/app.py`保留FastAPI适配层，供接口实验和自动化调用使用。它不会被打包进桌面EXE，也不会随桌面程序启动。

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
2. 在`backend/review_engine.py`增加场景审查函数，输入统一为`list[tuple[str, list[str]]]`。
3. 输出统一使用`Finding`，且至少包含一条`Evidence`。
4. 在`desktop.py`的`SCENARIOS`中注册场景入口。
5. 增加一个正确样本和至少三个错误样本。

后续应将当前Python函数式规则迁移为通用操作符，例如`required_document`、`regex_extract`、`between`、`equals_across_documents`和`sum_equals`。

## 9. EXE构建

执行：

```powershell
.\build.ps1
```

脚本会：

1. 创建`.venv`并安装`requirements-desktop.txt`；
2. 使用`mingjian.spec`生成单文件EXE；
3. 嵌入CustomTkinter主题、应用图标和场景包；
4. 计算SHA-256并写入校验文件；
5. 将EXE和校验文件同步到官网的下载目录。

PyInstaller明确排除FastAPI、Uvicorn、PyWebView、Starlette和Pydantic，桌面产物不包含Web运行时。

## 10. 验证

本次构建已验证：

- 原生窗口可独立启动；
- EXE进程没有监听TCP端口；
- 竞赛和合同规则均返回结构化Finding；
- 材料列表、风险详情、问题销项与文本报告导出可用；
- 官网下载文件与`dist/MingJian.exe`的SHA-256一致。

## 11. 已知限制

- 当前PDF解析只支持带文字层的原生PDF；扫描PDF需要后续接入PaddleOCR。
- 当前没有接入大模型，规则抽取和语义审查使用内置演示逻辑。
- DOC旧格式、XLS旧格式和图片尚未支持。
- 当前展示文本证据片段，尚未根据PDF坐标绘制真实页面高亮框。
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
