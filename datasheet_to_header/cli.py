from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .agent import AgentError, parse_with_agent
from .header import HeaderOptions, guard_from_filename, render_header
from .io import read_datasheet_text
from .models import ValidationError
from .parser import ParseError, parse_datasheet_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datasheet-to-header",
        description="Generate a C register header from a microcontroller datasheet excerpt.",
    )
    parser.add_argument("input", nargs="?", help="text/PDF datasheet excerpt, or '-' for stdin")
    parser.add_argument("-o", "--output", help="write header to this file")
    parser.add_argument("--stdout", action="store_true", help="write generated header to stdout")
    parser.add_argument("--name", help="override peripheral name")
    parser.add_argument("--base-address", help="override peripheral base address, e.g. 0x40013800")
    parser.add_argument("--macro-prefix", help="prefix every generated macro")
    parser.add_argument("--guard", help="override include guard")
    parser.add_argument("--lowercase-hex", action="store_true", help="format hex digits as lowercase")
    parser.add_argument("--no-base", action="store_true", help="omit the peripheral base macro")
    parser.add_argument("--no-suffix", action="store_true", help="omit the unsigned integer suffix")
    parser.add_argument("--use-agent", action="store_true", help="use smolagents extraction before rendering")
    parser.add_argument("--model", default="Qwen/Qwen2.5-Coder-32B-Instruct", help="Hugging Face model id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.input:
        print("error: input file is required unless '-' is used for stdin", file=sys.stderr)
        return 2
    if not args.stdout and not args.output:
        print("error: specify --stdout or --output", file=sys.stderr)
        return 2

    try:
        text = sys.stdin.read() if args.input == "-" else read_datasheet_text(args.input)
        if args.use_agent:
            peripheral = parse_with_agent(text, model_id=args.model)
        else:
            peripheral = parse_datasheet_text(
                text,
                peripheral_name=args.name,
                base_address=args.base_address,
            )

        guard = args.guard
        if not guard and args.output:
            guard = guard_from_filename(Path(args.output).name)
        header = render_header(
            peripheral,
            HeaderOptions(
                guard=guard,
                macro_prefix=args.macro_prefix,
                uppercase_hex=not args.lowercase_hex,
                include_base=not args.no_base,
                integer_suffix="" if args.no_suffix else "u",
            ),
        )
    except (OSError, RuntimeError, ParseError, ValidationError, AgentError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.stdout:
        print(header, end="")

    if args.output:
        Path(args.output).write_text(header, encoding="utf-8")

    return 0
