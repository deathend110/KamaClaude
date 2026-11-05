from __future__ import annotations

import asyncio
import json
import sys
import time

import kama_claude
from kama_claude.core.bus.commands import PongResult
from kama_claude.core.bus.envelope import JsonRpcError, JsonRpcSuccess
from kama_claude.core.config import KamaConfig


# 同步入口：运行 ping 协程，连接失败时打印错误并退出
def cmd_ping(config: KamaConfig) -> None:
    try:
        asyncio.run(_ping(config))
    except (ConnectionRefusedError, OSError):
        print(f"error: core not running ({config.host}:{config.port})", file=sys.stderr)
        sys.exit(1)


# 向 core 守护进程发送 ping 请求，打印 pong 响应及延迟
async def _ping(config: KamaConfig) -> None:
    t0 = time.monotonic()
    # 建立连接
    reader, writer = await asyncio.open_connection(config.host, config.port)

    # 在_ping函数下包装core.ping的具体req，此时是py dict
    req = {
        "jsonrpc": "2.0",
        "id": "cli-1",
        "method": "core.ping",
        "params": {"client": f"cli/{kama_claude.__version__}"},
    }

    # 将req字典序列化为json，添加\n，编码为TCP字节，写入连接发送缓冲区
    writer.write((json.dumps(req) + "\n").encode())
    await writer.drain()

    # 从连接流中读取一行响应，最多等待10s
    line = await asyncio.wait_for(reader.readline(), timeout=10.0)
    # 计算从CLI建立连接，发送请求，core处理请求，返回响应，CLI接受响应 的往来时间
    latency_ms = int((time.monotonic() - t0) * 1000)

    writer.close()
    await writer.wait_closed()

    # 这里是单独CLI进行响应解包的过程
    raw = json.loads(line)
    if "error" in raw:
        err = JsonRpcError.model_validate(raw)
        print(f"error: {err.error.code} {err.error.message}", file=sys.stderr)
        sys.exit(1)

    # 校验jsonRpc 成功响应的外层结构
    resp = JsonRpcSuccess.model_validate(raw)
    # 校验result是否符合PongResult。注意，通过模型校验不一定业务内容正确，可能只是模板正确，具体内容实际上需要更多约束
    result = PongResult.model_validate(resp.result)
    # 格式化输出result并加上CLI计时结果
    print(f"pong server={result.server_version} uptime={result.uptime_ms}ms latency={latency_ms}ms")
