import json
import logging
import time
import urllib.error
import urllib.request
from typing import Callable

from genai_worker.exceptions import GenAiException

log = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

PROMPT = (
    "Summarize the following document in at most 5 sentences. "
    "Write the summary in the same language as the document. "
    "Reply with the summary only.\n\n"
)


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float,
        max_retries: int,
        max_input_chars: int,
        urlopen: Callable = urllib.request.urlopen,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = api_key
        self._url = f"{base_url}/models/{model}:generateContent"
        self._timeout = timeout
        self._max_retries = max_retries
        self._max_input_chars = max_input_chars
        self._urlopen = urlopen
        self._sleep = sleep

    def summarize(self, text: str) -> str:
        if len(text) > self._max_input_chars:
            log.warning("Text has %d characters, truncating to %d", len(text), self._max_input_chars)
            text = text[: self._max_input_chars]
        body = json.dumps({"contents": [{"parts": [{"text": PROMPT + text}]}]}).encode("utf-8")
        return self._parse(self._post(body))

    def _post(self, body: bytes) -> dict:
        request = urllib.request.Request(
            self._url, data=body, method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": self._api_key},
        )
        for attempt in range(1, self._max_retries + 1):
            reason = ""
            try:
                with self._urlopen(request, timeout=self._timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as ex:
                reason = f"HTTP {ex.code}: {_error_message(ex)}"
                if ex.code not in _RETRYABLE_STATUS:
                    raise GenAiException(f"Gemini API rejected the request ({reason})") from ex
            except (urllib.error.URLError, TimeoutError, OSError) as ex:
                reason = f"network error: {ex}"
            except (json.JSONDecodeError, UnicodeDecodeError) as ex:
                raise GenAiException(f"Gemini API returned invalid JSON: {ex}") from ex

            if attempt == self._max_retries:
                raise GenAiException(f"Gemini API failed after {attempt} attempts ({reason})")
            delay = 2 ** attempt
            log.warning("Gemini API call failed (attempt %d/%d, %s), retrying in %ds",
                        attempt, self._max_retries, reason, delay)
            self._sleep(delay)
        raise GenAiException("Gemini API call was not attempted")

    @staticmethod
    def _parse(payload: dict) -> str:
        try:
            candidate = payload["candidates"][0]
            text = "".join(part.get("text", "") for part in candidate["content"]["parts"]).strip()
        except (KeyError, IndexError, TypeError, AttributeError) as ex:
            block = (payload.get("promptFeedback") or {}).get("blockReason") if isinstance(payload, dict) else None
            raise GenAiException(
                f"Gemini API returned no summary{f' (blocked: {block})' if block else ''}"
            ) from ex
        if not text:
            raise GenAiException("Gemini API returned an empty summary")
        return text


def _error_message(ex: urllib.error.HTTPError) -> str:
    try:
        return json.loads(ex.read().decode("utf-8"))["error"]["message"]
    except Exception:  # noqa: BLE001
        return ex.reason or "no details"
