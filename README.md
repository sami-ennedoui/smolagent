# 🤖 Embedded AI Agent: Datasheet-to-C Generator

An autonomous AI agent that parses microcontroller datasheet memory maps and automatically generates production-ready C header files (`.h`) for bare-metal embedded systems. 

This project bridges the gap between Large Language Models (LLMs) and hardware engineering, demonstrating how AI agents can automate tedious firmware development tasks like register configuration and memory mapping.

## ✨ Features
- **Autonomous Tool Use:** The agent uses Hugging Face `smolagents` to reason through datasheet text, calculate absolute hex addresses, and execute custom Python file-writing tools.
- **Zero-Compute Cloud Execution:** Powered by the `Qwen2.5-Coder-32B` model via the Hugging Face Serverless Inference API (requires no local GPU).
- **Secure Containerization:** Fully containerized using **Podman** (daemonless) and Python 3.12, ensuring a reproducible, secure, and isolated execution environment free of local dependency conflicts.

## 🛠️ Tech Stack
- **Framework:** Hugging Face `smolagents`
- **Model:** `Qwen2.5-Coder-32B-Instruct`
- **Environment:** Podman / Docker, Python 3.12
- **Security:** `python-dotenv` for API secret management

## 🚀 Quick Start

### 1. Prerequisites
- [Podman](https://podman.io/) (or Docker) installed on your system.
- A free Hugging Face API token.

### 2. Setup
Clone the repository and navigate into the project directory:
```bash
git clone https://github.com/YOUR_USERNAME/embedded-ai-agent.git
cd embedded-ai-agent
```

Create a `.env` file in the root directory and add your Hugging Face token (do not use quotation marks):
```env
HF_TOKEN=hf_your_token_here
```
*(Note: `.env` is included in `.gitignore` to prevent leaking credentials.)*

### 3. Build the Container
Build the daemonless container image:
```bash
podman build -t hardware-agent .
```

### 4. Run the Agent
Run the container. We map a volume (`-v`) with the `:Z` SELinux flag so the agent can safely export the generated `.h` file directly to your local host directory:
```bash
podman run --env-file .env -v "$(pwd):/app:Z" hardware-agent
```

## 📄 Example Output
Given a raw text snippet from a UART peripheral datasheet, the agent automatically calculates the offset math and generates `uart_regs.h`:

```c
#ifndef __UART_REGS_H__
#define __UART_REGS_H__

#define UART_DR         0x40002000
#define UART_SR         0x40002004
#define UART_BRR        0x40002008
#define UART_CR1        0x4000200c

#endif /* __UART_REGS_H__ */
```

## 🔮 Future Roadmap
- [ ] **PDF Parsing Tool:** Integrate `PyMuPDF` to allow the agent to read raw component datasheets directly.
- [ ] **CAN Bus Matrix Automation:** Expand the agent to ingest `.dbc` or Excel CAN matrices to automatically generate C-structs and bit-masking logic for Automotive/BMS applications.
- [ ] **Verilog Testbench Generation:** Add custom tools for FPGA workflows to auto-generate Icarus Verilog testbenches from SystemVerilog module definitions.
### Note
This has been devolopped and tested for Fedora Linux Workstation version 43.
