# 第三方组件

发行包包含以下第三方模型与运行时：

## Qwen2.5-0.5B-Instruct-GGUF

- 项目：Qwen
- 来源：https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF
- 文件：`qwen2.5-0.5b-instruct-q4_k_m.gguf`
- 许可证：Apache License 2.0

模型许可证副本随构建输入保存在 `models/LICENSE-Qwen2.5`，并由 PyInstaller 放入发行包。

## llama.cpp

- 项目：ggml-org/llama.cpp
- 来源：https://github.com/ggml-org/llama.cpp
- 许可证：MIT License

运行时的许可证文件随 `runtime/llama/` 一同放入发行包。LLVM OpenMP 的许可证保存在 `runtime/llama/LICENSE-LLVM-OpenMP`。
