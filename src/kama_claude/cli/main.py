from __future__ import annotations

import argparse
import sys

from kama_claude.cli.commands.echo import cmd_echo
from kama_claude.cli.commands.ping import cmd_ping
from kama_claude.cli.commands.version import cmd_version
from kama_claude.core.config import get_config
from kama_claude.core.logging_setup import setup_logging


# CLI 主入口：解析命令行参数并分发到对应子命令
def main() -> None:
    # 一级解析器，kama是help中出现的命令名，如下：
    # usage: kama [-h] [--version] {ping,echo}
    # 实际上uv run kama 的kama能调用这个main文件来自:
    # pyproject.toml中的 kama = "kama_claude.cli.main:main"
    parser = argparse.ArgumentParser(prog="kama", description="KamaClaude CLI")

    # 声明一个参数：--version，这是主命令kama的选项
    parser.add_argument("--version", action="store_true", help="Print version and exit")

    # 创建子命令组，把子命令的名字保存在解析结果args的command属性中：args.command
    subparsers = parser.add_subparsers(dest="command")
    # 为子命令组注册一个具体的子命令，ping
    subparsers.add_parser("ping", help="Ping the core daemon")

    # 为子命令组注册一个具体的子命令，echo同时获取其解析器
    echo_parser  = subparsers.add_parser("echo", help="echo the send content")
    # 在 echo 的规则下声明一个位置参数。这里的 "text" 自动成为属性名，保存用户传入的具体文本：
    echo_parser.add_argument("text", help="specific text")

    # 参数解析
    args = parser.parse_args()

    if args.version:
        cmd_version()
        return

    if args.command == "ping":
        config = get_config()
        setup_logging(config)
        cmd_ping(config)
    elif args.command == "echo":
        config = get_config()
        setup_logging(config)
        cmd_echo(config, args.text)
    else:
        parser.print_help()
        sys.exit(1)
