from __future__ import annotations

import re

from .models import Peripheral, Register, ValidationError, normalize_c_identifier


class ParseError(ValueError):
    """Raised when datasheet text does not contain a parseable register map."""


_HEX_TOKEN = r"(?:0x[0-9A-Fa-f][0-9A-Fa-f_]*|[0-9A-Fa-f][0-9A-Fa-f_]*[Hh])"
_IDENT_TOKEN = r"[A-Za-z_][A-Za-z0-9_]*(?:\s*/\s*[A-Za-z_][A-Za-z0-9_]*)*"
_RESERVED_NAMES = {"RES", "RESERVED", "RESERVEDBITS"}

_BASE_PATTERNS = [
    re.compile(
        rf"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b[^\n]{{0,80}}?"
        rf"\bbase\s+address\b[^\n:=>]*[:=>]?\s*(?P<base>{_HEX_TOKEN})",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bbase\s+address\b[^\n:=>]*[:=>]?\s*(?P<base>{_HEX_TOKEN})",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)_BASE\b[^\n=]*=\s*(?P<base>{_HEX_TOKEN})",
        re.IGNORECASE,
    ),
]

_REGISTER_PATTERNS = [
    re.compile(
        rf"^\s*[-*]\s*(?P<name>{_IDENT_TOKEN})\b.*?"
        rf"\b(?:address\s+)?offset\b\s*[:=]?\s*(?P<offset>{_HEX_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"^\s*(?P<name>{_IDENT_TOKEN})\b\s*(?:\([^)]*\))?\s*[:\-]?\s*"
        rf"\b(?:address\s+)?offset\b\s*[:=]?\s*(?P<offset>{_HEX_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"^\s*(?P<name>{_IDENT_TOKEN})\b\s+(?P<offset>{_HEX_TOKEN})\b(?:\s|$)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"^\s*(?P<offset>{_HEX_TOKEN})\b\s+(?P<name>{_IDENT_TOKEN})\b(?:\s|$)",
        re.IGNORECASE,
    ),
]

_PARENS_REGISTER_RE = re.compile(r"\((?P<name>[A-Za-z_][A-Za-z0-9_]*)\)")
_ADDRESS_OFFSET_RE = re.compile(
    rf"\baddress\s+offset\b\s*[:=]?\s*(?P<offset>{_HEX_TOKEN})\b", re.IGNORECASE
)
_ABSOLUTE_REGISTER_RE = re.compile(
    rf"^\s*(?P<address>{_HEX_TOKEN})\b\s+.*?\((?P<name>[A-Za-z_][A-Za-z0-9_]*)\)",
    re.IGNORECASE,
)


def parse_datasheet_text(
    text: str,
    *,
    peripheral_name: str | None = None,
    base_address: int | str | None = None,
) -> Peripheral:
    """Parse a small register-map excerpt from datasheet text.

    The parser intentionally handles common register-map patterns rather than
    attempting to understand an entire reference manual in one pass. For full
    PDFs, extract the relevant peripheral section first or provide
    ``base_address`` and ``peripheral_name`` overrides.
    """
    text = _collapse_spaced_hex(text)
    if not text.strip():
        raise ParseError("input is empty")

    discovered_name, discovered_base = _find_base(text)
    name = peripheral_name or discovered_name or "PERIPHERAL"
    base = _parse_int(base_address) if base_address is not None else discovered_base
    if base is None:
        raise ParseError("missing base address; pass --base-address or include one in the text")

    registers = _find_registers(text, base)
    if not registers:
        raise ParseError("no register offsets found")

    try:
        return Peripheral.from_registers(name=name, base_address=base, registers=registers)
    except ValidationError as exc:
        raise ParseError(str(exc)) from exc


def _find_base(text: str) -> tuple[str | None, int | None]:
    for pattern in _BASE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        name = match.groupdict().get("name")
        return name, _parse_int(match.group("base"))
    return None, None


def _find_registers(text: str, base_address: int) -> list[Register]:
    registers: list[Register] = []
    pending_name: str | None = None

    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not line or _should_skip_line(line):
            continue

        title_name = _extract_title_register_name(line)
        if title_name:
            pending_name = title_name

        offset_match = _ADDRESS_OFFSET_RE.search(line)
        if offset_match and pending_name:
            registers.extend(_registers_from_name(pending_name, _parse_int(offset_match.group("offset"))))
            pending_name = None
            continue

        absolute_match = _ABSOLUTE_REGISTER_RE.match(line)
        if absolute_match:
            address = _parse_int(absolute_match.group("address"))
            if address >= base_address:
                registers.extend(_registers_from_name(absolute_match.group("name"), address - base_address))
                continue

        for pattern in _REGISTER_PATTERNS:
            match = pattern.match(line)
            if not match:
                continue
            name = match.group("name")
            offset = _parse_int(match.group("offset"))
            if _looks_like_register_name(name):
                registers.extend(_registers_from_name(name, offset))
                break

    return registers


def _clean_line(line: str) -> str:
    line = _collapse_spaced_hex(line)
    line = line.replace("|", " ")
    line = line.replace("\u2013", "-").replace("\u2014", "-")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def _collapse_spaced_hex(text: str) -> str:
    pattern = re.compile(r"0x([0-9A-Fa-f]{1,4})\s+([0-9A-Fa-f]{4,8})(?![0-9A-Fa-f])")
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub(lambda match: f"0x{match.group(1)}{match.group(2)}", text)
    return text


def _should_skip_line(line: str) -> bool:
    lowered = line.lower()
    if lowered.startswith("#"):
        return True
    skip_phrases = (
        "base address",
        "reset value",
        "register summary",
        "register map",
        "address offset",
        "offset name",
        "name offset",
    )
    return any(phrase in lowered for phrase in skip_phrases) and not _ADDRESS_OFFSET_RE.search(line)


def _extract_title_register_name(line: str) -> str | None:
    if "register" not in line.lower():
        return None
    matches = _PARENS_REGISTER_RE.findall(line)
    if not matches:
        return None
    candidate = matches[-1]
    return candidate if _looks_like_register_name(candidate) else None


def _looks_like_register_name(name: str) -> bool:
    cleaned = re.sub(r"\s+", "", name).upper()
    if cleaned in _RESERVED_NAMES:
        return False
    if cleaned.startswith("0X"):
        return False
    if len(cleaned) < 2:
        return False
    try:
        normalize_c_identifier(cleaned.replace("/", "_"))
    except ValidationError:
        return False
    return True


def _registers_from_name(name: str, offset: int) -> list[Register]:
    registers: list[Register] = []
    for part in re.split(r"\s*/\s*", name):
        part = part.strip()
        if _looks_like_register_name(part):
            registers.append(Register(name=part, offset=offset))
    return registers


def _parse_int(value: int | str) -> int:
    if isinstance(value, int):
        return value

    cleaned = value.strip().lower().replace("_", "").replace(" ", "")
    if cleaned.endswith("h"):
        return int(cleaned[:-1], 16)
    if cleaned.startswith("0x"):
        return int(cleaned[2:], 16)
    if any(ch in "abcdef" for ch in cleaned):
        return int(cleaned, 16)
    return int(cleaned, 10)
