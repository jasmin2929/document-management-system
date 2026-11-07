import shutil
import subprocess
import unittest
from pathlib import Path

from ocr_worker.exceptions import OcrProcessingException
from ocr_worker.processing.ocr_engine import OcrEngine

# A minimal one-page PDF that shows "Hello World" in 24 pt Helvetica.
HELLO_WORLD_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\nBT /F1 24 Tf 50 70 Td (Hello World) Tj ET\nendstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)


class FakeTools:
    """Stands in for subprocess.run: pretends to be Ghostscript and Tesseract.

    Records every command, so tests can check the arguments.
    """

    def __init__(self, pages=2, page_text="Hello World"):
        self.pages = pages
        self.page_text = page_text
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(command)
        if command[0] == "gs":
            # Ghostscript writes one image per page into the folder given in -sOutputFile
            pattern = next(arg for arg in command if arg.startswith("-sOutputFile=")).split("=", 1)[1]
            for number in range(1, self.pages + 1):
                Path(pattern.replace("%03d", f"{number:03d}")).write_bytes(b"png")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout=f"{self.page_text} {Path(command[1]).name}\n", stderr="")


class ExtractTextTest(unittest.TestCase):
    def test_text_of_all_pages_is_joined_in_page_order(self):
        engine = OcrEngine(runner=FakeTools(pages=2))

        text = engine.extract_text(HELLO_WORLD_PDF)

        self.assertEqual("Hello World page-001.png\n\nHello World page-002.png", text)

    def test_ghostscript_runs_in_safe_mode_with_page_limit(self):
        tools = FakeTools()
        OcrEngine(dpi=200, max_pages=5, runner=tools).extract_text(HELLO_WORLD_PDF)

        gs_command = tools.commands[0]
        self.assertEqual("gs", gs_command[0])
        self.assertIn("-dSAFER", gs_command)
        self.assertIn("-r200", gs_command)
        self.assertIn("-dLastPage=5", gs_command)

    def test_tesseract_runs_once_per_page_with_language(self):
        tools = FakeTools(pages=3)
        OcrEngine(language="eng", runner=tools).extract_text(HELLO_WORLD_PDF)

        tesseract_commands = [c for c in tools.commands if c[0] == "tesseract"]
        self.assertEqual(3, len(tesseract_commands))
        self.assertEqual(["stdout", "-l", "eng"], tesseract_commands[0][2:])

    def test_temporary_files_are_deleted_afterwards(self):
        tools = FakeTools()
        OcrEngine(runner=tools).extract_text(HELLO_WORLD_PDF)

        pdf_path = Path(tools.commands[0][-1])
        self.assertFalse(pdf_path.parent.exists())

    def test_content_that_is_not_a_pdf_is_rejected(self):
        tools = FakeTools()
        with self.assertRaisesRegex(OcrProcessingException, "not a PDF"):
            OcrEngine(runner=tools).extract_text(b"MZ\x90\x00 an exe file")
        self.assertEqual([], tools.commands)  # the tools are never started

    def test_no_rendered_pages_raises(self):
        with self.assertRaisesRegex(OcrProcessingException, "did not produce any page"):
            OcrEngine(runner=FakeTools(pages=0)).extract_text(HELLO_WORLD_PDF)


class ToolErrorTest(unittest.TestCase):
    def _engine_failing_with(self, error):
        def runner(command, **kwargs):
            raise error
        return OcrEngine(runner=runner)

    def test_missing_tool_raises_processing_exception(self):
        engine = self._engine_failing_with(FileNotFoundError("gs"))
        with self.assertRaisesRegex(OcrProcessingException, "Ghostscript is not installed"):
            engine.extract_text(HELLO_WORLD_PDF)

    def test_tool_error_includes_exit_code_and_message(self):
        engine = self._engine_failing_with(subprocess.CalledProcessError(1, ["gs"], stderr="Error: /syntaxerror"))
        with self.assertRaisesRegex(OcrProcessingException, "exit code 1: Error: /syntaxerror"):
            engine.extract_text(HELLO_WORLD_PDF)

    def test_timeout_raises_processing_exception(self):
        engine = self._engine_failing_with(subprocess.TimeoutExpired(["gs"], 120))
        with self.assertRaisesRegex(OcrProcessingException, "did not finish within"):
            engine.extract_text(HELLO_WORLD_PDF)

    def test_check_tools_returns_both_versions(self):
        def runner(command, **kwargs):
            output = "10.05.1\n" if command[0] == "gs" else "tesseract 5.5.0\n leptonica-1.84.1\n"
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

        self.assertEqual("Ghostscript 10.05.1, tesseract 5.5.0", OcrEngine(runner=runner).check_tools())

    def test_check_tools_raises_if_tool_is_missing(self):
        with self.assertRaisesRegex(OcrProcessingException, "not installed"):
            self._engine_failing_with(FileNotFoundError("gs")).check_tools()


@unittest.skipUnless(shutil.which("gs") and shutil.which("tesseract"), "Ghostscript/Tesseract not installed")
class RealToolsIntegrationTest(unittest.TestCase):
    """Runs the real Ghostscript and Tesseract (they are installed in the Docker image)."""

    def test_hello_world_pdf_is_recognized(self):
        text = OcrEngine(language="eng").extract_text(HELLO_WORLD_PDF)

        self.assertIn("Hello World", text)

    def test_check_tools_reports_installed_versions(self):
        versions = OcrEngine().check_tools()

        self.assertRegex(versions, r"^Ghostscript \d+\.\d+.*, tesseract \d+\.\d+")


if __name__ == "__main__":
    unittest.main()
