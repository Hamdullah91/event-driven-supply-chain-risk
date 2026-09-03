from __future__ import annotations

import html
import re


class FilingTextCleaner:
    """
    Cleans parsed SEC filing text before NLP processing.
    """

    _MULTIPLE_SPACES = re.compile(r"[ \t]+")
    _MULTIPLE_NEWLINES = re.compile(r"\n{3,}")
    _CONTROL_CHARACTERS = re.compile(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
    )

    def clean(self, text: str) -> str:
        if not text:
            return ""

        text = html.unescape(text)

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        text = text.replace("\xa0", " ")
        text = text.replace("\u200b", "")
        text = text.replace("\ufeff", "")

        text = self._CONTROL_CHARACTERS.sub("", text)

        lines: list[str] = []

        for line in text.splitlines():
            line = self._MULTIPLE_SPACES.sub(" ", line).strip()

            if line:
                lines.append(line)
            else:
                lines.append("")

        cleaned = "\n".join(lines)

        cleaned = self._MULTIPLE_NEWLINES.sub("\n\n", cleaned)

        return cleaned.strip()