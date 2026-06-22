import unittest

from datasheet_to_header.header import HeaderOptions, render_header
from datasheet_to_header.models import Peripheral, Register, ValidationError


class HeaderTests(unittest.TestCase):
    def test_renders_hex_addresses_and_include_guard(self) -> None:
        peripheral = Peripheral.from_registers(
            "UART",
            0x40002000,
            [
                Register("UART_DR", 0x00),
                Register("UART_SR", 0x04),
                Register("UART_BRR", 0x08),
                Register("UART_CR1", 0x0C),
            ],
        )

        header = render_header(peripheral, HeaderOptions(guard="UART_REGS_H"))

        self.assertEqual(
            header,
            """#ifndef UART_REGS_H
#define UART_REGS_H

#define UART_BASE  0x40002000u
#define UART_DR    0x40002000u
#define UART_SR    0x40002004u
#define UART_BRR   0x40002008u
#define UART_CR1   0x4000200Cu

#endif /* UART_REGS_H */
""",
        )

    def test_macro_prefix_handles_generic_register_names(self) -> None:
        peripheral = Peripheral.from_registers(
            "SERCOM0",
            0x42000800,
            [Register("CTRLA", 0x00), Register("DATA", 0x28)],
        )

        header = render_header(peripheral, HeaderOptions(macro_prefix="samd21"))

        self.assertIn("#define SAMD21_SERCOM0_BASE  0x42000800u", header)
        self.assertIn("#define SAMD21_CTRLA         0x42000800u", header)
        self.assertIn("#define SAMD21_DATA          0x42000828u", header)

    def test_conflicting_duplicate_macro_is_error(self) -> None:
        peripheral = Peripheral.from_registers(
            "UART",
            0x40002000,
            [Register("UART_BASE", 0x00)],
        )

        with self.assertRaises(ValidationError):
            render_header(peripheral)


if __name__ == "__main__":
    unittest.main()
