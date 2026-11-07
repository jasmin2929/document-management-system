"""Processing layer: turns a PDF into text with Ghostscript and Tesseract.

Two command line tools do the work (both are installed in the Docker image):

1. **Ghostscript** (``gs``) renders every PDF page into a PNG image.
   Tesseract cannot read PDFs, only images.
2. **Tesseract** (``tesseract``) recognizes the text on each image (OCR).

Both are started with :func:`subprocess.run` and an argument *list* (no shell),
so a file name can never be interpreted as an additional command.

Run it by hand inside the container::

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

# Every PDF file starts with these bytes ("magic number").
PDF_SIGNATURE = b"%PDF-"


class OcrEngine:
    """Extracts the text of a PDF document.

    Knows nothing about RabbitMQ or the object storage: it receives the PDF
    content as bytes and returns the recognized text.
    """

    def __init__(
        self,
        language: str = "deu+eng",
        dpi: int = 300,
        max_pages: int = 50,
        timeout_seconds: float = 120.0,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ) -> None:
        """Create the engine.

        Args:
            language: Tesseract language(s), e.g. ``"deu+eng"``.
            dpi: Resolution of the rendered page images.
            max_pages: Pages after this one are ignored.
            timeout_seconds: Maximum runtime of one tool call.
            runner: Starts the external tools. Injected so unit tests can
                replace it and do not need Ghostscript or Tesseract installed.
        """
        self._language = language
        self._dpi = dpi
        self._max_pages = max_pages
        self._timeout = timeout_seconds
        self._run = runner

    def check_tools(self) -> str:
        """Check that Ghostscript and Tesseract are installed (called once at startup).

        Returns:
            The tool versions, e.g. ``"Ghostscript 10.05.1, tesseract 5.5.0"``.

        Raises:
            OcrProcessingException: If one of the tools is missing or broken.
        """
        gs_version = self._execute(["gs", "--version"], "Ghostscript").strip()
        # Tesseract prints several lines (libraries used); the first one is its own version
        tesseract_version = self._execute(["tesseract", "--version"], "Tesseract").strip().splitlines()[0]
        return f"Ghostscript {gs_version}, {tesseract_version}"

    def extract_text(self, pdf_content: bytes) -> str:
        """Run the OCR on a PDF document.

        Args:
            pdf_content: The raw bytes of the PDF file.

        Returns:
            The recognized text of all pages, separated by empty lines.

        Raises:
            OcrProcessingException: If the content is not a PDF or one of the
                tools fails, times out or is not installed.
        """
        if not pdf_content.startswith(PDF_SIGNATURE):
            raise OcrProcessingException("Content is not a PDF document")

        # Everything is written to a private temporary folder that is deleted afterwards.
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
        """Convert each PDF page into a grayscale PNG image with Ghostscript."""
        command = [
            "gs",
            "-dSAFER",  # forbids the PDF to read/write other files: protects against malicious PDFs
            "-dBATCH", "-dNOPAUSE", "-dQUIET",  # run without user interaction
            "-sDEVICE=pnggray",  # grayscale is enough for OCR and keeps the images small
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
        """Run Tesseract on one page image and return its text."""
        # "stdout" tells Tesseract to print the text instead of writing a file
        command = ["tesseract", str(image_path), "stdout", "-l", self._language]
        return self._execute(command, "Tesseract")

    def _execute(self, command: List[str], tool: str) -> str:
        """Run an external tool and translate its errors into this layer's exception."""
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


def _main(argv: List[str]) -> int:  # pragma: no cover - manual demo, covered by the integration test
    """Print the text of the PDF file given as the first argument."""
    if len(argv) != 2:
        print("Usage: python -m ocr_worker.processing.ocr_engine <file.pdf>")
        return 2
    logging.basicConfig(level="INFO", format="%(levelname)-5s [%(name)s] %(message)s")
    print(OcrEngine().extract_text(Path(argv[1]).read_bytes()))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_main(sys.argv))
