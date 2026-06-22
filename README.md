# Datasheet-to-C header generator

Generate C register-address headers from microcontroller datasheet excerpts. You
give it a register map, in text or PDF, and it produces a `.h` file with the base
address and every register address as a `#define`.

The design keeps the language model away from anything safety critical. A
hallucinated register address can brick hardware, so the address arithmetic and
validation are always done in plain Python, never by the model.

> Note. This deterministic core has been reused in a larger project. The genuinely
> agentic version, where a `smolagents` agent searches the STM32H7 reference manual
> and drafts a page-cited register header, lives in
> [sami-ennedoui/stm32-datasheet-rag](https://github.com/sami-ennedoui/stm32-datasheet-rag)
> (`app/agent.py` and `app/regtools.py`). This repository keeps the standalone
> command line tool.

## How it works

There are two paths to extract the register map:

- A deterministic parser that recognises common register-map text patterns with
  regular expressions. This is the default and needs no network or token.
- An optional `smolagents` extraction mode for messy text. Here the model only
  returns structured data, register names and offsets relative to the base. It
  does not compute absolute addresses and does not write files.

In both paths the same Python code validates the names as C identifiers, rejects
conflicting duplicates, computes each absolute address as base plus offset, and
renders the header.

## Features

- Parses base addresses written as `0x4000_2000`, `0x4001 3800`, or `4004_A04Ch`.
- Parses register maps in `NAME 0xOFFSET`, `0xOFFSET NAME`, and `Address offset: 0x..` styles.
- Expands alias registers such as `UARTRSR/UARTECR`.
- Deduplicates repeated same-offset entries and rejects conflicting duplicate register names.
- Renders deterministic C headers with include guards, hex addresses, and optional macro prefixes.
- Reads text files directly, and PDF files when PyMuPDF is installed.

## Quick start

Run from the repository, no token needed for the deterministic path:

```bash
python -m datasheet_to_header tests/fixtures/synthetic_uart.txt --name UART -o uart_regs.h
```

Or print to stdout:

```bash
python -m datasheet_to_header tests/fixtures/stm32_usart1_excerpt.txt --stdout --no-base
```

## Example output

```c
#ifndef UART_REGS_H
#define UART_REGS_H

#define UART_BASE  0x40002000u
#define UART_DR    0x40002000u
#define UART_SR    0x40002004u
#define UART_BRR   0x40002008u
#define UART_CR1   0x4000200Cu

#endif /* UART_REGS_H */
```

## Optional agent mode

Agent mode helps when the deterministic parser cannot read a messy table. It needs
a free Hugging Face token in `HF_TOKEN`:

```bash
export HF_TOKEN=hf_your_token_here
python -m datasheet_to_header datasheet_excerpt.txt --use-agent -o regs.h
```

The model is used only to extract structured data. The project validates register
names, offsets, duplicates, and the C header output locally.

## Tested datasheet fixtures

The test suite includes small excerpts based on public vendor documentation:

- STMicroelectronics STM32F103 RM0008 USART register map
- Microchip SAM D21/DA1 SERCOM USART register summary
- Raspberry Pi RP2040 UART register list
- NXP KL25 PORT memory map example

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Container

Build:

```bash
podman build -t hardware-agent .
```

Run against a mounted repository, passing the input file:

```bash
podman run --rm -v "$(pwd):/work:Z" hardware-agent \
  /work/tests/fixtures/synthetic_uart.txt --name UART -o /work/uart_regs.h
```

Use Docker by replacing `podman` with `docker`, and drop `:Z` if your platform
does not use SELinux labels.

## Scope

This is an assistant, not a certified generator. Always confirm the generated
addresses against the official datasheet before using them on hardware.

Developed and tested on Fedora Linux Workstation 43.
