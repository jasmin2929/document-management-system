"""PDF to text: Ghostscript renders each page to a PNG, Tesseract reads the text from it.

Manual run inside the container:
    python -m ocr_worker.processing.ocr_engine /tmp/HelloWorld.pdf
"""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, List

from ocr_worker.exceptions import OcrProcessingException

log = logging.getLogger(__name__)

PDF_SIGNATURE = b"%PDF-"


class OcrEngine:
    def __init__(
        self,
        language: str = "deu+eng",
        dpi: int = 300,
        max_pages: int = 50,
        timeout_seconds: float = 120.0,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ) -> None:
        self._language = language
        self._dpi = dpi
        self._max_pages = max_pages
        self._timeout = timeout_seconds
        self._run = runner

    def check_tools(self) -> str:
        """Return the tool versions; raises OcrProcessingException if a tool is missing."""
        gs_version = self._execute(["gs", "--version"], "Ghostscript").strip()
        tesseract_version = self._execute(["tesseract", "--version"], "Tesseract").strip().splitlines()[0]
        return f"Ghostscript {gs_version}, {tesseract_version}"

    def extract_text(self, pdf_content: bytes) -> str:
        """Return the text of all pages, separated by empty lines."""
        if not pdf_content.startswith(PDF_SIGNATURE):
            raise OcrProcessingException("Content is not a PDF document")

        with tempfile.TemporaryDirectory(prefix="ocr-") as work_dir:
            pdf_path = Path(work_dir) / "input.pdf"
            pdf_path.write_bytes(pdf_content)

            pages = self._render_pages(pdf_path, Path(work_dir))
            log.info("Rendered %d page(s) with Ghostscript, starting Tesseract (%s)", len(pages), self._language)

            texts = [self._recognize(page) for page in pages]

        text = "\n\n".join(t.strip() for t in texts if t.strip())
        log.info("OCR finished: %d characters recognized", len(text))
        return text

    def _render_pages(self, pdf_path: Path, work_dir: Path) -> List[Path]:
        command = [
            "gs",
            "-dSAFER",  # the PDF may not read or write other files
            "-dBATCH", "-dNOPAUSE", "-dQUIET",
            "-sDEVICE=pnggray",
            f"-r{self._dpi}",
            "-dFirstPage=1", f"-dLastPage={self._max_pages}",
            f"-sOutputFile={work_dir / 'page-%03d.png'}",
            str(pdf_path),
        ]
        self._execute(command, "Ghostscript")

        pages = sorted(work_dir.glob("page-*.png"))
        if not pages:
            raise OcrProcessingException("Ghostscript did not produce any page images")
        return pages

    def _recognize(self, image_path: Path) -> str:
        return self._execute(["tesseract", str(image_path), "stdout", "-l", self._language], "Tesseract")

    def _execute(self, command: List[str], tool: str) -> str:
        # Argument list, no shell: a file name can never become a command.
        try:
            result = self._run(command, capture_output=True, text=True, timeout=self._timeout, check=True)
        except FileNotFoundError as ex:
            raise OcrProcessingException(f"{tool} is not installed ('{command[0]}' not found)") from ex
        except subprocess.TimeoutExpired as ex:
            raise OcrProcessingException(f"{tool} did not finish within {self._timeout} seconds") from ex
        except subprocess.CalledProcessError as ex:
            details = (ex.stderr or "").strip()[:500]
            raise OcrProcessingException(f"{tool} failed with exit code {ex.returncode}: {details}") from ex
        return result.stdout


def _main(argv: List[str]) -> int:  # pragma: no cover - manual demo
    if len(argv) != 2:
        print("Usage: python -m ocr_worker.processing.ocr_engine <file.pdf>")
        return 2
    logging.basicConfig(level="INFO", format="%(levelname)-5s [%(name)s] %(message)s")
    print(OcrEngine().extract_text(Path(argv[1]).read_bytes()))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_main(sys.argv))
