import os
import sys
from smolagents import CodeAgent, HfApiModel, tool
from dotenv import load_dotenv
@tool
def generate_c_header(registers: dict, filename: str) -> str:
    """
    Generates a C header file from a dictionary of register names and addresses.
    
    Args:
        registers: A dictionary mapping register names to their hex addresses.
        filename: The output filename (e.g., 'timer_regs.h').
    """
    try:
        # Create standard C include guards
        guard = f"__{filename.upper().replace('.', '_')}__"
        
        with open(filename, 'w') as f:
            f.write(f"#ifndef {guard}\n")
            f.write(f"#define {guard}\n\n")
            
            for name, addr in registers.items():
                f.write(f"#define {name:<15} {addr}\n")
                
            f.write(f"\n#endif /* {guard} */\n")
            
        return f"Success: Wrote {len(registers)} registers to {filename}"
    
    except Exception as e:
        return f"Error writing file: {str(e)}"

#load token from .env
def main():
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("Error: HF_TOKEN environment variable not set.")
        print("Run: export HF_TOKEN='your_token_here'")
        sys.exit(1)

    # Initialize the LLM
    model = HfApiModel(
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        token=hf_token
    )

    # Initialize the agent with the custom tool
    agent = CodeAgent(tools=[generate_c_header], model=model)

    datasheet_snippet = """
    UART Peripheral Memory Map:
    Base Address: 0x4000_2000
    Registers:
    - UART_DR (Data Register): Offset 0x00
    - UART_SR (Status Register): Offset 0x04
    - UART_BRR (Baud Rate Register): Offset 0x08
    - UART_CR1 (Control Register 1): Offset 0x0C
    """

    prompt = (
        f"Parse the following datasheet snippet. Calculate the absolute hex addresses "
        f"for all registers by adding their offsets to the base address. "
        f"Use the generate_c_header tool to create 'uart_regs.h'.\n\n"
        f"Datasheet:\n{datasheet_snippet}"
    )

    print("Executing hardware agent workflow...")
    agent.run(prompt)


if __name__ == "__main__":
    main()
