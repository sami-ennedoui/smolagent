from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datasheet_to_header.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


class CliTests(unittest.TestCase):
    def test_cli_writes_expected_header(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "uart_regs.h"

            exit_code = main(
                [
                    str(FIXTURES / "synthetic_uart.txt"),
                    "--name",
                    "UART",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                (FIXTURES / "uart_regs_expected.h").read_text(encoding="utf-8"),
            )

    def test_cli_stdout(self) -> None:
        stdout = StringIO()

        with redirect_stdout(stdout):
            exit_code = main(
                [
                    str(FIXTURES / "stm32_usart1_excerpt.txt"),
                    "--stdout",
                    "--no-base",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("#define USART_SR    0x40013800u", stdout.getvalue())
        self.assertIn("#define USART_GTPR  0x40013818u", stdout.getvalue())

    def test_failed_parse_does_not_write_output(self) -> None:
        with TemporaryDirectory() as tmpdir:
            bad_input = Path(tmpdir) / "bad.txt"
            output = Path(tmpdir) / "bad.h"
            bad_input.write_text("UART_DR offset 0x00", encoding="utf-8")
            stderr = StringIO()

            with redirect_stderr(stderr):
                exit_code = main([str(bad_input), "--output", str(output)])

            self.assertEqual(exit_code, 1)
            self.assertFalse(output.exists())
            self.assertIn("missing base address", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
