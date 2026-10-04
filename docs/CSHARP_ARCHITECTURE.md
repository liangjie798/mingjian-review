# C# 桌面端架构

明鉴桌面端使用 C#、.NET 8 与 WPF 开发。发布包采用 Windows x64 自包含单文件模式，最终用户不需要安装 .NET SDK、运行时或其他开发环境。

## 项目结构

```text
src/MingJian.Desktop/
├── App.xaml                         全局颜色、字体与控件样式
├── MainWindow.xaml                 审查、合同对比和指南页面
├── MainWindow.xaml.cs              页面交互、主题切换与报告导出
├── SettingsWindow.xaml             大模型设置窗口
├── SettingsWindow.xaml.cs          提供商切换、模型列表和配置保存
├── Models.cs                       领域模型与风险等级
└── Services/
    ├── DocumentParser.cs           PDF、DOCX、XLSX 和文本解析
    ├── ReviewEngine.cs             竞赛与合同确定性规则
    └── ModelService.cs             本地模型与云模型协议适配
```

自动化测试位于 `tests/MingJian.Desktop.Tests/`。场景规则配置位于 `scenario-packs/`，官网位于 `website/`。

## 审查流程

1. 用户从左侧选择通用竞赛、数学建模、互联网+、挑战杯或合同审查场景。
2. `DocumentParser` 在本地提取所有材料文本。
3. `ReviewEngine` 对全部文本执行确定性规则，生成风险、证据和建议。
4. 用户启用模型增强时，`ModelService` 截取最多约 6000 个字符的材料样本交给所选模型。
5. 模型结论必须通过文件名、页码、风险级别和原文摘录校验，才能进入结果列表。
6. 用户可以逐条查看证据，并把结果导出为 Markdown 报告。

规则审查始终覆盖全部可提取文本。模型调用失败不会丢失规则审查结果。

## 文件解析

| 格式 | 实现 |
|---|---|
| PDF | PdfPig |
| DOCX | Open XML SDK |
| XLSX | Open XML SDK |
| TXT、MD、CSV、JSON | .NET 文本读取 |

扫描版 PDF 没有文本层，需要先进行 OCR。解析工作在线程池中执行，避免阻塞 WPF 界面。

## 模型接口

桌面端支持以下调用方式：

- 内置 Qwen2.5 GGUF，通过 llama.cpp 子进程离线运行。
- OpenAI 兼容协议，可连接 OpenAI、DeepSeek、通义千问、智谱、Kimi、硅基流动、豆包、OpenRouter 和自定义服务。
- Anthropic Messages API。
- Google Gemini generateContent API。
- Ollama `/api/chat` 本地接口。

模型配置保存在当前 Windows 用户的 `%LOCALAPPDATA%\MingJian\settings.json`。API 密钥不会写入仓库。

## 界面与动效

`App.xaml` 定义统一的颜色、圆角、边框、字体和按钮交互状态。界面当前提供深色与浅色两套主题，切换时替换动态画刷，不需要重新创建窗口。

主页面切换采用透明度和横向位移动画。按钮按下时提供轻微缩放反馈，审查期间显示非阻塞进度状态。动画只使用 WPF 合成属性，避免持续修改布局尺寸。

## 合同对比

合同对比由 DiffPlex 完成。两个版本在本地解析和比较：

- 红色表示甲方版本删除内容。
- 绿色表示乙方版本新增内容。
- 琥珀色表示修改内容。

单份合同上限为 20 万字符，防止超大文本造成长时间占用。

## 开发与构建

```powershell
dotnet restore MingJian.sln
dotnet test MingJian.sln
dotnet run --project src\MingJian.Desktop\MingJian.Desktop.csproj
```

生成发布版：

```powershell
.\build.ps1
```

构建脚本会先运行测试，再生成 `dist-wpf/MingJian-AI.exe` 和 SHA-256 校验文件。若电脑没有 .NET 8 SDK，脚本会把独立 SDK 下载到 `.tools/dotnet`，不会修改系统环境变量。

内置模型与 llama.cpp 不提交到 Git 仓库。构建前应准备：

```text
models/qwen2.5-0.5b-instruct-q4_k_m.gguf
models/LICENSE-Qwen2.5
runtime/llama/llama-cli.exe
runtime/llama/*.dll
runtime/llama/LICENSE-llama.cpp
```

## 发布检查

1. 运行全部自动化测试。
2. 生成自包含单文件 EXE。
3. 在 Windows 10 或 Windows 11 上启动发布文件。
4. 检查内置模型、文件拖放、两类审查、主题切换、合同对比与报告导出。
5. 将 EXE 和校验文件上传到 GitHub Releases。
