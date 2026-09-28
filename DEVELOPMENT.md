# 开发与发布

## 技术结构

- 桌面 UI：PySide6
- 文件解析：PyMuPDF、python-docx、openpyxl
- 本地推理：Qwen2.5 GGUF + llama.cpp
- 云端模型：OpenAI 兼容协议、Anthropic Messages API、Gemini generateContent API
- 打包：PyInstaller 单文件模式
- 官网：原生 HTML、CSS、JavaScript，由 GitHub Pages 发布

## 本地开发

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe desktop.py
```

应用先对全部材料执行确定性规则，再把最多约 6000 个字符的文本样本交给模型。模型结论只有在文件名、页码、风险级别和原文证据通过校验后才会进入结果列表。

合同版本对比使用 `difflib.SequenceMatcher` 对中英文混合文本分词比较。差异视图在本机生成，不调用模型接口；红色表示甲方版删除内容，绿色表示乙方版新增内容，琥珀色表示双方修改内容。

## 准备内置模型

创建以下本地文件。它们已被 `.gitignore` 排除：

```text
models/qwen2.5-0.5b-instruct-q4_k_m.gguf
models/LICENSE-Qwen2.5
runtime/llama/llama-cli.exe
runtime/llama/*.dll
runtime/llama/LICENSE-llama.cpp
```

模型使用 Qwen 官方的 Qwen2.5-0.5B-Instruct-GGUF Q4_K_M。运行时使用 llama.cpp Windows CPU x64 发行包。

## 构建 EXE

```powershell
.\build.ps1
```

输出：

```text
dist/MingJian-AI.exe
dist/MingJian-AI.exe.sha256.txt
```

单文件包含约 469 MB 模型和 CPU 推理运行时，因此首次启动需要等待 PyInstaller 解压。发布文件超过 GitHub 普通仓库的单文件限制，应上传到 GitHub Releases。

## 发布

1. 运行规则与本地模型测试。
2. 运行 `build.ps1`。
3. 在干净的 Windows 10 或 Windows 11 机器上启动 EXE。
4. 上传 EXE 与 SHA-256 文件到新的 GitHub Release。
5. 官网使用 `releases/latest/download/MingJian-AI.exe`，无需随版本修改链接。

## 官网预览

```powershell
py -m http.server 4173 --directory website
```

打开 `http://127.0.0.1:4173`。推送到默认分支后，GitHub Actions 会发布 `website/`。
