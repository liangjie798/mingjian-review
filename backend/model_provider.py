from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal


Provider = Literal["openai", "ollama"]
Scenario = Literal["competition", "contract"]


@dataclass(slots=True)
class ModelConfig:
    enabled: bool = False
    provider: Provider = "openai"
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    timeout: int = 120


def _json_request(url: str, timeout: int, payload: dict[str, Any] | None = None, api_key: str = "") -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data)
    request.add_header("Content-Type", "application/json")
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"模型接口返回 HTTP {error.code}：{detail[:160]}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError("无法连接模型接口，请检查地址、网络或本地服务状态。") from error


def list_models(config: ModelConfig) -> list[str]:
    base = config.base_url.rstrip("/")
    if config.provider == "ollama":
        response = _json_request(f"{base}/api/tags", min(config.timeout, 8))
        return [item.get("name", "") for item in response.get("models", []) if item.get("name")]
    response = _json_request(f"{base}/models", min(config.timeout, 8), api_key=config.api_key)
    return [item.get("id", "") for item in response.get("data", []) if item.get("id")]


def _chat(config: ModelConfig, messages: list[dict[str, str]]) -> str:
    base = config.base_url.rstrip("/")
    if config.provider == "ollama":
        response = _json_request(
            f"{base}/api/chat",
            config.timeout,
            {"model": config.model, "stream": False, "format": "json", "messages": messages,
             "options": {"temperature": 0.1, "num_ctx": 32768}},
        )
        return str(response.get("message", {}).get("content", ""))
    response = _json_request(
        f"{base}/chat/completions",
        config.timeout,
        {"model": config.model, "temperature": 0.1, "messages": messages},
        config.api_key,
    )
    choices = response.get("choices", [])
    return str(choices[0].get("message", {}).get("content", "")) if choices else ""


def analyze_documents(
    config: ModelConfig,
    scenario: Scenario,
    documents: list[tuple[str, list[str]]],
) -> list[dict[str, Any]]:
    remaining = 36_000
    blocks: list[str] = []
    for name, pages in documents:
        page_blocks: list[str] = []
        for page_number, page in enumerate(pages, start=1):
            cleaned = re.sub(r"\s+", " ", page).strip()
            if not cleaned or remaining <= 0:
                continue
            snippet = cleaned[: min(remaining, 8_000)]
            remaining -= len(snippet)
            page_blocks.append(f"[第{page_number}页] {snippet}")
        blocks.append(f"\n### 文件：{name}\n" + "\n".join(page_blocks))

    scene = "大学生竞赛材料" if scenario == "competition" else "合同材料"
    schema = (
        '{"findings":[{"severity":"blocking|high|medium|info","title":"标题",'
        '"detail":"说明","file":"准确文件名","page":1,"excerpt":"原文短句",'
        '"suggestion":"可执行建议"}]}'
    )
    messages = [
        {"role": "system", "content": "你是严谨的中文材料审查助手。只根据原文指出可验证的问题，不得虚构条款、数字或页码。只输出 JSON。"},
        {"role": "user", "content": f"场景：{scene}\n最多返回8个高价值问题，没有可靠问题时返回空数组。\n结构：{schema}\n材料：\n" + "\n".join(blocks)},
    ]
    content = re.sub(r"<think>[\s\S]*?</think>", "", _chat(config, messages)).strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content).strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError("模型返回内容不是有效 JSON，请重试或调整模型。") from error
    items = parsed.get("findings", []) if isinstance(parsed, dict) else parsed
    if not isinstance(items, list):
        raise RuntimeError("模型返回结构不符合审查协议。")
    return [item for item in items[:8] if isinstance(item, dict)]
