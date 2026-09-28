from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


Provider = Literal[
    "embedded", "openai", "deepseek", "siliconflow", "dashscope",
    "zhipu", "moonshot", "volcengine", "openrouter", "anthropic",
    "gemini", "ollama", "custom",
]
Scenario = Literal["competition", "contract"]

OPENAI_COMPATIBLE_PROVIDERS = {
    "openai", "deepseek", "siliconflow", "dashscope", "zhipu",
    "moonshot", "volcengine", "openrouter", "custom",
}


@dataclass(slots=True)
class ModelConfig:
    enabled: bool = True
    provider: Provider = "embedded"
    base_url: str = ""
    model: str = "Qwen2.5-0.5B-Instruct Q4_K_M"
    api_key: str = ""
    timeout: int = 180


def _json_request(
    url: str,
    timeout: int,
    payload: dict[str, Any] | None = None,
    api_key: str = "",
    headers: dict[str, str] | None = None,
) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data)
    request.add_header("Content-Type", "application/json")
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"模型接口返回 HTTP {error.code}：{detail[:160]}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError("无法连接模型接口，请检查地址、网络或本地服务状态。") from error


def list_models(config: ModelConfig) -> list[str]:
    if config.provider == "embedded":
        model_path, runtime_path = _embedded_paths()
        if not model_path.exists() or not runtime_path.exists():
            raise RuntimeError("内置模型文件不完整，请重新下载安装包。")
        return ["Qwen2.5-0.5B-Instruct Q4_K_M"]
    base = config.base_url.rstrip("/")
    if config.provider == "ollama":
        response = _json_request(f"{base}/api/tags", min(config.timeout, 8))
        return [item.get("name", "") for item in response.get("models", []) if item.get("name")]
    if config.provider == "anthropic":
        response = _json_request(
            f"{base}/models", min(config.timeout, 8),
            headers={"x-api-key": config.api_key, "anthropic-version": "2023-06-01"},
        )
        return [item.get("id", "") for item in response.get("data", []) if item.get("id")]
    if config.provider == "gemini":
        response = _json_request(
            f"{base}/models", min(config.timeout, 8),
            headers={"x-goog-api-key": config.api_key},
        )
        return [str(item.get("name", "")).removeprefix("models/") for item in response.get("models", []) if item.get("name")]
    response = _json_request(f"{base}/models", min(config.timeout, 8), api_key=config.api_key)
    return [item.get("id", "") for item in response.get("data", []) if item.get("id")]


def _chat(config: ModelConfig, messages: list[dict[str, str]]) -> str:
    if config.provider == "embedded":
        return _embedded_chat(config, messages)
    base = config.base_url.rstrip("/")
    if config.provider == "ollama":
        response = _json_request(
            f"{base}/api/chat",
            config.timeout,
            {"model": config.model, "stream": False, "format": "json", "messages": messages,
             "options": {"temperature": 0.1, "num_ctx": 32768}},
        )
        return str(response.get("message", {}).get("content", ""))
    if config.provider == "anthropic":
        system = "\n\n".join(item["content"] for item in messages if item["role"] == "system")
        conversation = [item for item in messages if item["role"] != "system"]
        response = _json_request(
            f"{base}/messages",
            config.timeout,
            {"model": config.model, "max_tokens": 1200, "temperature": 0.1,
             "system": system, "messages": conversation},
            headers={"x-api-key": config.api_key, "anthropic-version": "2023-06-01"},
        )
        return "".join(str(item.get("text", "")) for item in response.get("content", []) if item.get("type") == "text")
    if config.provider == "gemini":
        system = "\n\n".join(item["content"] for item in messages if item["role"] == "system")
        contents = [
            {"role": "model" if item["role"] == "assistant" else "user",
             "parts": [{"text": item["content"]}]}
            for item in messages if item["role"] != "system"
        ]
        response = _json_request(
            f"{base}/models/{config.model}:generateContent",
            config.timeout,
            {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
             "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}},
            headers={"x-goog-api-key": config.api_key},
        )
        candidates = response.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "".join(str(item.get("text", "")) for item in parts)
    response = _json_request(
        f"{base}/chat/completions",
        config.timeout,
        {"model": config.model, "temperature": 0.1, "messages": messages},
        config.api_key,
    )
    choices = response.get("choices", [])
    return str(choices[0].get("message", {}).get("content", "")) if choices else ""


def _resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def _embedded_paths() -> tuple[Path, Path]:
    root = _resource_root()
    return (
        root / "models" / "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        root / "runtime" / "llama" / "llama-cli.exe",
    )


def _embedded_chat(config: ModelConfig, messages: list[dict[str, str]]) -> str:
    model_path, runtime_path = _embedded_paths()
    if not model_path.exists() or not runtime_path.exists():
        raise RuntimeError("内置模型文件不完整，请重新下载安装包。")

    system = next((item["content"] for item in messages if item["role"] == "system"), "")
    prompt = "\n\n".join(item["content"] for item in messages if item["role"] != "system")
    threads = max(2, min(8, (os.cpu_count() or 4) - 1))
    command = [
        str(runtime_path), "-m", str(model_path), "-sys", system, "-p", prompt,
        "-st", "-n", "900", "-c", "8192", "-t", str(threads),
        "--temp", "0.1", "--no-display-prompt", "--no-show-timings",
        "--simple-io", "--log-disable",
    ]
    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(config.timeout, 180),
            startupinfo=startupinfo,
            creationflags=creationflags,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("内置模型推理超时，请减少材料数量后重试。") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-240:]
        raise RuntimeError(f"内置模型运行失败：{detail or '未知错误'}")
    return result.stdout.strip()


def analyze_documents(
    config: ModelConfig,
    scenario: Scenario,
    documents: list[tuple[str, list[str]]],
) -> list[dict[str, Any]]:
    # The bundled 0.5B model has an 8K working context in the desktop profile.
    # Rules still inspect every page; the model receives a focused text sample.
    remaining = 6_000
    blocks: list[str] = []
    for name, pages in documents:
        page_blocks: list[str] = []
        for page_number, page in enumerate(pages, start=1):
            cleaned = re.sub(r"\s+", " ", page).strip()
            if not cleaned or remaining <= 0:
                continue
            snippet = cleaned[: min(remaining, 3_000)]
            remaining -= len(snippet)
            page_blocks.append(f"[第{page_number}页] {snippet}")
        blocks.append(f"\n### 文件：{name}\n" + "\n".join(page_blocks))

    scene = "大学生竞赛材料" if scenario == "competition" else "合同材料"
    file_names = [name for name, _ in documents]
    messages = [
        {"role": "system", "content": "你是严谨的中文材料审查员。只根据原文指出可验证的问题，不得虚构条款、数字或页码。输出JSON，所有字段必须填写真实内容，禁止照抄字段说明。"},
        {"role": "user", "content": (
            f"审查场景：{scene}。找出最多8个高价值问题，没有可靠问题时返回空数组。"
            "返回一个findings数组。每项必须包含severity、title、detail、file、page、excerpt、suggestion。"
            "severity只能是blocking、high、medium或info，page必须是整数，file必须使用材料中的准确文件名，excerpt必须是原文短句。"
            f"可用文件名：{json.dumps(file_names, ensure_ascii=False)}\n材料：\n" + "\n".join(blocks)
        )},
    ]
    content = re.sub(r"<think>[\s\S]*?</think>", "", _chat(config, messages)).strip()
    parsed: Any = None
    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)```", content, flags=re.IGNORECASE)
    for block in reversed(fenced):
        try:
            parsed = json.loads(block.strip())
            break
        except json.JSONDecodeError:
            continue
    decoder = json.JSONDecoder()
    candidates = [match.start() for match in re.finditer(r"\{\s*\"findings\"", content)]
    for start in reversed(candidates) if parsed is None else []:
        try:
            parsed, _ = decoder.raw_decode(content[start:])
            break
        except json.JSONDecodeError:
            continue
    if parsed is None:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise RuntimeError("模型返回内容不是有效 JSON，请重试或调整模型。") from error
    items = parsed.get("findings", []) if isinstance(parsed, dict) else parsed
    if not isinstance(items, list):
        raise RuntimeError("模型返回结构不符合审查协议。")
    page_lookup = {name: pages for name, pages in documents}
    sanitized: list[dict[str, Any]] = []
    placeholders = {"标题", "说明", "准确文件名", "原文短句", "可执行建议"}
    for item in items[:8]:
        if not isinstance(item, dict) or item.get("file") not in page_lookup:
            continue
        severity = str(item.get("severity", "medium"))
        if severity not in {"blocking", "high", "medium", "info"}:
            severity = "medium"
        page_match = re.search(r"\d+", str(item.get("page", 1)))
        page = int(page_match.group()) if page_match else 1
        pages = page_lookup[item["file"]]
        page = max(1, min(page, len(pages)))
        source_text = pages[page - 1]
        excerpt = str(item.get("excerpt", "")).strip()
        if excerpt not in source_text:
            parts = [part.strip() for part in re.split(r"[，,。！？；]", excerpt) if len(part.strip()) >= 6]
            excerpt = next((part for part in parts if part in source_text), "")
        title = str(item.get("title", "")).strip()
        detail = str(item.get("detail", "")).strip()
        suggestion = str(item.get("suggestion", "")).strip()
        if not excerpt or not title or not detail or not suggestion or {title, detail, excerpt, suggestion} & placeholders:
            continue
        normalized = {
            "severity": severity,
            "title": title,
            "detail": detail,
            "file": item["file"],
            "page": page,
            "excerpt": excerpt[:240],
            "suggestion": suggestion,
        }
        if not any(existing["title"] == title and existing["file"] == item["file"] and existing["page"] == page for existing in sanitized):
            sanitized.append(normalized)
    return sanitized
