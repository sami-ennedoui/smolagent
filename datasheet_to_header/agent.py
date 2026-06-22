from __future__ import annotations

import json
import os
import re

from .models import Peripheral, Register, ValidationError


class AgentError(RuntimeError):
    """Raised when optional LLM extraction fails."""


def parse_with_agent(
    text: str,
    *,
    model_id: str = "Qwen/Qwen2.5-Coder-32B-Instruct",
    token: str | None = None,
) -> Peripheral:
    """Use smolagents as an optional extractor, then validate locally.

    The agent is not allowed to write files or perform address arithmetic for the
    renderer. It returns structured data, and this module validates that data
    before the header layer sees it.
    """
    try:
        from smolagents import CodeAgent, HfApiModel
    except ImportError as exc:
        raise AgentError("smolagents is not installed") from exc

    token = token or os.getenv("HF_TOKEN")
    if not token:
        raise AgentError("HF_TOKEN is required when --use-agent is set")

    model = HfApiModel(model_id=model_id, token=token)
    agent = CodeAgent(tools=[], model=model, add_base_tools=False)
    prompt = _agent_prompt(text)
    response = agent.run(prompt)
    payload = _extract_json(str(response))

    try:
        registers = [
            Register(
                name=item["name"],
                offset=_parse_agent_int(item["offset"]),
                description=item.get("description"),
            )
            for item in payload["registers"]
        ]
        return Peripheral.from_registers(
            name=payload["name"],
            base_address=_parse_agent_int(payload["base_address"]),
            registers=registers,
        )
    except (KeyError, TypeError, ValidationError, ValueError) as exc:
        raise AgentError(f"agent returned invalid register data: {exc}") from exc


def _agent_prompt(text: str) -> str:
    return (
        "Extract one microcontroller peripheral register map from the datasheet "
        "text below. Return JSON only with this schema: "
        '{"name": "USART1", "base_address": "0x40013800", '
        '"registers": [{"name": "USART_SR", "offset": "0x00", '
        '"description": "status register"}]}. '
        "Use offsets relative to the peripheral base. Do not calculate absolute "
        "register addresses in the JSON.\n\n"
        f"{text}"
    )


def _extract_json(response: str) -> dict:
    match = re.search(r"\{.*\}", response, flags=re.DOTALL)
    if not match:
        raise AgentError("agent response did not contain JSON")
    return json.loads(match.group(0))


def _parse_agent_int(value: int | str) -> int:
    if isinstance(value, int):
        return value
    cleaned = value.strip().lower().replace("_", "").replace(" ", "")
    if cleaned.startswith("0x"):
        return int(cleaned[2:], 16)
    if cleaned.endswith("h"):
        return int(cleaned[:-1], 16)
    if any(ch in "abcdef" for ch in cleaned):
        return int(cleaned, 16)
    return int(cleaned, 10)
