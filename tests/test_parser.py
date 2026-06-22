from pathlib import Path
import unittest

from datasheet_to_header.parser import ParseError, parse_datasheet_text


FIXTURES = Path(__file__).parent / "fixtures"


class ParserTests(unittest.TestCase):
    def test_parses_synthetic_uart_snippet_with_underscore_hex(self) -> None:
        text = (FIXTURES / "synthetic_uart.txt").read_text(encoding="utf-8")

        peripheral = parse_datasheet_text(text, peripheral_name="UART")

        self.assertEqual(peripheral.name, "UART")
        self.assertEqual(peripheral.base_address, 0x40002000)
        self.assertEqual(
            {register.name: register.absolute_address(peripheral.base_address) for register in peripheral.registers},
            {
                "UART_DR": 0x40002000,
                "UART_SR": 0x40002004,
                "UART_BRR": 0x40002008,
                "UART_CR1": 0x4000200C,
            },
        )

    def test_parses_stm32_usart_register_map(self) -> None:
        text = (FIXTURES / "stm32_usart1_excerpt.txt").read_text(encoding="utf-8")

        peripheral = parse_datasheet_text(text)

        self.assertEqual(peripheral.name, "USART1")
        self.assertEqual(peripheral.base_address, 0x40013800)
        self.assertEqual(
            {register.name: register.absolute_address(peripheral.base_address) for register in peripheral.registers},
            {
                "USART_SR": 0x40013800,
                "USART_DR": 0x40013804,
                "USART_BRR": 0x40013808,
                "USART_CR1": 0x4001380C,
                "USART_CR2": 0x40013810,
                "USART_CR3": 0x40013814,
                "USART_GTPR": 0x40013818,
            },
        )

    def test_parses_microchip_sercom_usart_summary_and_dedupes_same_offset(self) -> None:
        text = (FIXTURES / "microchip_samd21_sercom0_usart_excerpt.txt").read_text(encoding="utf-8")

        peripheral = parse_datasheet_text(text)

        self.assertEqual(peripheral.name, "SERCOM0")
        self.assertEqual(peripheral.base_address, 0x42000800)
        self.assertEqual(
            {register.name: register.absolute_address(peripheral.base_address) for register in peripheral.registers},
            {
                "CTRLA": 0x42000800,
                "CTRLB": 0x42000804,
                "CTRLC": 0x42000808,
                "BAUD": 0x4200080C,
                "RXPL": 0x4200080E,
                "INTENCLR": 0x42000814,
                "INTENSET": 0x42000816,
                "INTFLAG": 0x42000818,
                "STATUS": 0x4200081A,
                "SYNCBUSY": 0x4200081C,
                "DATA": 0x42000828,
                "DBGCTRL": 0x42000830,
            },
        )

    def test_parses_rp2040_uart_alias_registers(self) -> None:
        text = (FIXTURES / "rp2040_uart0_excerpt.txt").read_text(encoding="utf-8")

        peripheral = parse_datasheet_text(text)
        addresses = {
            register.name: register.absolute_address(peripheral.base_address)
            for register in peripheral.registers
        }

        self.assertEqual(peripheral.name, "UART0")
        self.assertEqual(peripheral.base_address, 0x40034000)
        self.assertEqual(addresses["UARTDR"], 0x40034000)
        self.assertEqual(addresses["UARTRSR"], 0x40034004)
        self.assertEqual(addresses["UARTECR"], 0x40034004)
        self.assertEqual(addresses["UARTDMACR"], 0x40034048)

    def test_parses_nxp_h_suffix_absolute_addresses(self) -> None:
        text = (FIXTURES / "nxp_kl25_portb_excerpt.txt").read_text(encoding="utf-8")

        peripheral = parse_datasheet_text(text)
        addresses = {
            register.name: register.absolute_address(peripheral.base_address)
            for register in peripheral.registers
        }

        self.assertEqual(peripheral.name, "PORTB")
        self.assertEqual(peripheral.base_address, 0x4004A000)
        self.assertEqual(addresses["PORTB_PCR0"], 0x4004A000)
        self.assertEqual(addresses["PORTB_PCR1"], 0x4004A004)
        self.assertEqual(addresses["PORTB_PCR18"], 0x4004A048)
        self.assertEqual(addresses["PORTB_PCR19"], 0x4004A04C)

    def test_missing_base_address_is_error(self) -> None:
        with self.assertRaises(ParseError):
            parse_datasheet_text("UART_DR offset 0x00")

    def test_conflicting_duplicate_register_is_error(self) -> None:
        with self.assertRaises(ParseError):
            parse_datasheet_text(
                """
                TEST base address: 0x40000000
                REG_A 0x00
                REG_A 0x04
                """
            )


if __name__ == "__main__":
    unittest.main()
