from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import webbrowser

# PyInstaller窗口模式没有控制台输出流，Uvicorn初始化日志时仍会访问它们。
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import uvicorn

from backend.app import app


def free_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if probe.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def run_server(port: int) -> None:
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def wait_until_ready(port: int, timeout: float = 12.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("本地服务启动超时")


def main() -> None:
    parser = argparse.ArgumentParser(description="明鉴多场景材料审查")
    parser.add_argument("--server-only", action="store_true", help="只启动本地Web服务")
    parser.add_argument("--port", type=int, default=8765, help="本地服务端口")
    args = parser.parse_args()
    port = free_port(args.port)

    if args.server_only:
        run_server(port)
        return

    server = threading.Thread(target=run_server, args=(port,), daemon=True)
    server.start()
    wait_until_ready(port)
    url = f"http://127.0.0.1:{port}"

    try:
        import webview

        webview.create_window("明鉴 · 材料智能审查", url, width=1440, height=920, min_size=(1024, 680))
        webview.start(debug=False)
    except Exception:
        webbrowser.open(url)
        server.join()


if __name__ == "__main__":
    main()
