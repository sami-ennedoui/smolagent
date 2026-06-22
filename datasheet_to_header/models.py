from __future__ import annotations

from dataclasses import dataclass
import re


class ValidationError(ValueError):
    """Raised when parsed register data cannot safely be rendered as C."""


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def normalize_c_identifier(value: str) -> str:
    """Return a stable C macro identifier for a datasheet register name."""
    value = value.strip()
    if not value:
        raise ValidationError("empty identifier")

    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", value)
    normalized = re.sub(r"_+", "_", normalized).strip("_").upper()
    if not normalized:
        raise ValidationError(f"invalid identifier: {value!r}")
    if normalized[0].isdigit():
        normalized = f"_{normalized}"
    if not _IDENTIFIER_RE.match(normalized):
        raise ValidationError(f"invalid identifier after normalization: {value!r}")
    return normalized


@dataclass(frozen=True)
class Register:
    name: str
    offset: int
    description: str | None = None

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise ValidationError(f"negative offset for {self.name}: {self.offset}")
        normalize_c_identifier(self.name)

    @property
    def c_name(self) -> str:
        return normalize_c_identifier(self.name)

    def absolute_address(self, base_address: int) -> int:
        return base_address + self.offset


@dataclass(frozen=True)
class Peripheral:
    name: str
    base_address: int
    registers: tuple[Register, ...]

    def __post_init__(self) -> None:
        if self.base_address < 0:
            raise ValidationError(f"negative base address for {self.name}")
        normalize_c_identifier(self.name)
        if not self.registers:
            raise ValidationError(f"{self.name} has no registers")

        seen: dict[str, int] = {}
        for register in self.registers:
            previous_offset = seen.get(register.c_name)
            if previous_offset is not None and previous_offset != register.offset:
                raise ValidationError(
                    f"register {register.c_name} appears at both "
                    f"0x{previous_offset:X} and 0x{register.offset:X}"
                )
            seen[register.c_name] = register.offset

    @property
    def c_name(self) -> str:
        return normalize_c_identifier(self.name)

    @classmethod
    def from_registers(
        cls, name: str, base_address: int, registers: list[Register]
    ) -> "Peripheral":
        deduped: dict[str, Register] = {}
        for register in registers:
            existing = deduped.get(register.c_name)
            if existing is None:
                deduped[register.c_name] = register
                continue
            if existing.offset != register.offset:
                raise ValidationError(
                    f"register {register.c_name} appears at both "
                    f"0x{existing.offset:X} and 0x{register.offset:X}"
                )

        ordered = sorted(deduped.values(), key=lambda item: item.offset)
        return cls(name=name, base_address=base_address, registers=tuple(ordered))
