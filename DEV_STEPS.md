# 明鉴开发步骤

## 1. 开发目标

构建一个可在Windows本地运行的多场景材料审查应用。首个可提交版本完整支持大学生竞赛审查和合同审查，所有结论包含规则、文件、页码、原文和整改建议。

比赛交付包括：

- React产品界面；
- FastAPI本地服务；
- Windows安装版和免安装版；
- GitHub Pages产品官网；
- GitHub Releases安装包；
- 细粒度Git提交、Prompt记录和10分钟复现说明。

## 2. 开源项目采用策略

| 能力 | 参考项目 | 使用方式 |
|---|---|---|
| 中文OCR与复杂版面 | PaddleOCR / PP-StructureV3 | 作为扫描件和表格解析适配器 |
| Office与PDF统一解析 | Docling | 作为可替换解析适配器进行对比测试 |
| 结构化大模型输出 | Instructor + Pydantic | 约束规则、事实和审查结果Schema |
| 页码引用与证据展示 | doc_assistant | 借鉴证据与解释分离的交互 |
| 引用真实性检查 | Ethos | 借鉴确定性证据验证的数据格式 |
| 文档能力评测 | OfficeComprehensionBench / DocScope | 借鉴问题、证据和评分组织方式 |

不复制完整开源应用。规则确认、事实对照、审查执行、整改销项和场景包机制由本项目自行实现。

## 3. 当前代码结构

```text
.
├── src/                         React前端
│   ├── App.tsx                  场景首页与审查工作台
│   ├── data.ts                  MVP演示数据
│   ├── types.ts                 前端类型
│   └── styles.css               设计系统与响应式样式
├── backend/
│   ├── app.py                   FastAPI接口
│   └── requirements.txt         Python依赖
├── scenario-packs/
│   ├── competition/             竞赛审查场景包
│   └── contract/                合同审查场景包
├── 材料审查智能体项目资料.md      产品研究与需求资料
└── DEV_STEPS.md                 本文档
```

## 4. 阶段一：跑通产品原型

目标：让评委无需上传真实文件即可体验完整审查逻辑。

1. 完成场景首页、竞赛审查和合同审查工作台。
2. 提供内置模拟材料和预期问题。
3. 实现问题筛选、证据定位、整改建议和销项。
4. 接入FastAPI的场景列表与演示审查接口。
5. 增加加载、空数据和接口错误状态。
6. 验证桌面和手机布局。

验收条件：用户能从首页进入两个场景，在5分钟内理解并完成一次模拟审查。

## 5. 阶段二：接入真实文档解析

目标：支持PDF、DOCX和XLSX，并保留页码和区域坐标。

1. 定义统一`ParsedDocument`格式：页面、文本块、表格、坐标、置信度。
2. 使用PyMuPDF解析原生PDF。
3. 使用python-docx和openpyxl处理Word与Excel。
4. 接入PaddleOCR PP-StructureV3处理扫描PDF、表格和印章区域。
5. 编写解析适配器接口，允许后续切换Docling或MinerU。
6. 保存原始文件哈希和解析器版本，保证结果可追溯。
7. 用10份公开或自制材料比较解析准确率和耗时。

验收条件：每个文本块都能回到文件、页码和区域坐标；解析失败不会产生伪造文本。

## 6. 阶段三：实现规则和事实引擎

目标：让大模型负责理解，程序负责可靠执行。

1. 使用Pydantic定义`Rule`、`Fact`、`Evidence`和`Finding`。
2. 从赛事通知或企业制度中抽取候选规则。
3. 在规则中心让用户确认、修改、启用或停用规则。
4. 把姓名、主体、金额、日期等写入统一事实表。
5. 实现确定性执行器：
   - 必交材料集合；
   - 字段非空；
   - 规范化精确匹配；
   - 日期范围；
   - Decimal金额重算；
   - 页数、大小和文件类型。
6. 对语义规则采用检索加结构化大模型输出。
7. 低置信度结果进入人工复核，不自动判定失败。

验收条件：确定性规则重复运行结果一致；每个Finding至少包含一条有效证据。

## 7. 阶段四：完成两个场景

### 竞赛审查

1. 规则提取：参赛对象、人数、组别、材料、格式和截止时间。
2. 资格计算：学籍、学校类别和团队人数。
3. 跨文档比对：名称、成员、指导教师和学校。
4. 整改看板与提交清单。

### 合同审查

1. 主体名称和信用代码一致性。
2. 金额大小写、分项合计、税率和付款比例。
3. 日期、交付、验收和质保条款。
4. 正文与报价单、附件之间的冲突。
5. 企业内部规则检查。

合同板块只提供辅助检查与风险提示，不输出最终法律结论。

## 8. 阶段五：测试与评测

1. 制作30组材料包，累计注入至少100个问题。
2. 保存问题类型、规则、证据文件、页码和预期结论。
3. 分别统计字段准确率、问题精确率、问题召回率和证据定位准确率。
4. 单独统计阻断项漏检率。
5. 记录每组材料处理时间和人工复核时间。
6. 增加模糊、旋转、缺页、空表格和例外条件测试。

建议目标：确定性规则精确率不低于95%，跨文档关键字段问题召回率不低于90%，证据页定位准确率不低于90%。

## 9. 阶段六：桌面打包

采用`PySide6 + Python审查引擎 + PyInstaller`：

1. 原生窗口直接调用Python审查函数。
2. 文件解析与规则执行放入后台线程。
3. PyInstaller打包窗口、解析器、主题和应用图标。
4. 明确排除FastAPI、Uvicorn和PyWebView。
5. 生成免安装单文件EXE。
6. 输出SHA-256校验值并同步官网文件。

## 10. 阶段七：官网与发布

1. 在独立`website/`目录制作产品介绍页。
2. 使用GitHub Actions发布到GitHub Pages。
3. 把EXE和ZIP上传到GitHub Releases。
4. 官网下载按钮链接到最新Release。
5. 展示版本、文件大小、校验值、系统要求和隐私说明。

## 11. Git与Prompt记录方式

每个提交只完成一个清晰功能，例如：

```text
feat(ui): add scenario selection home
feat(review): add evidence-linked finding panel
feat(api): add scenario and demo review endpoints
feat(parser): add page-aware PDF adapter
feat(rules): add deterministic amount validator
fix(evidence): preserve page coordinates after OCR rotation
```

至少保存三条完整Prompt链：

1. 场景包和规则Schema设计；
2. 文档解析与证据坐标修复；
3. 跨文件一致性审查和误报修复。

## 12. 10分钟复现目标

最终README应提供：

```powershell
git clone <repository-url>
cd <repository>
npm install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app:app
npm run dev
```

同时提供`.env.example`、固定依赖版本、内置样本和无需API密钥的演示模式。
