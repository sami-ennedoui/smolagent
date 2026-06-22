from __future__ import annotations

from dataclasses import dataclass
import re

from .models import Peripheral, ValidationError, normalize_c_identifier


@dataclass(frozen=True)
class HeaderOptions:
    guard: str | None = None
    macro_prefix: str | None = None
    hex_width: int = 8
    uppercase_hex: bool = True
    include_base: bool = True
    integer_suffix: str = "u"


def render_header(peripheral: Peripheral, options: HeaderOptions | None = None) -> str:
    options = options or HeaderOptions()
    guard = options.guard or f"{peripheral.c_name}_REGS_H"
    guard = normalize_c_identifier(guard)

    prefix = ""
    if options.macro_prefix:
        prefix = normalize_c_identifier(options.macro_prefix)
        if not prefix.endswith("_"):
            prefix += "_"

    macro_names: set[str] = set()
    rows: list[tuple[str, str]] = []

    if options.include_base:
        base_macro = f"{prefix}{peripheral.c_name}_BASE"
        rows.append((base_macro, _format_hex(peripheral.base_address, options)))
        macro_names.add(base_macro)

    for register in peripheral.registers:
        macro = f"{prefix}{register.c_name}"
        if macro in macro_names:
            raise ValidationError(f"duplicate macro name: {macro}")
        macro_names.add(macro)
        rows.append((macro, _format_hex(register.absolute_address(peripheral.base_address), options)))

    column_width = max(len(name) for name, _ in rows) + 1
    lines = [
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
    ]
    for macro, value in rows:
        lines.append(f"#define {macro:<{column_width}} {value}")
    lines.extend(["", f"#endif /* {guard} */", ""])
    return "\n".join(lines)


def _format_hex(value: int, options: HeaderOptions) -> str:
    digits = f"{value:0{options.hex_width}X}"
    if not options.uppercase_hex:
        digits = digits.lower()
    return f"0x{digits}{options.integer_suffix}"


def guard_from_filename(filename: str) -> str:
    stem = re.sub(r"[^0-9A-Za-z_]+", "_", filename).strip("_")
    return normalize_c_identifier(stem)
