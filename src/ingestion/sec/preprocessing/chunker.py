from __future__ import annotations

import re


class TextChunker:
    """
    Splits SEC filing sections into overlapping text chunks.

    Chunking is character-based but attempts to stop at natural
    sentence/paragraph boundaries.
    """

    def __init__(
        self,
        chunk_size: int = 2000,
        overlap: int = 250,
        minimum_chunk_size: int = 200,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.minimum_chunk_size = minimum_chunk_size

    def split(self, text: str) -> list[str]:
        text = text.strip()

        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            target_end = min(start + self.chunk_size, text_length)

            if target_end < text_length:
                end = self._find_boundary(
                    text=text,
                    start=start,
                    target_end=target_end,
                )
            else:
                end = target_end

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            new_start = max(end - self.overlap, start + 1)

            start = self._move_to_word_boundary(text, new_start)

        return self._merge_small_final_chunk(chunks)

    def _find_boundary(
        self,
        text: str,
        start: int,
        target_end: int,
    ) -> int:
        search_start = max(
            start + self.minimum_chunk_size,
            target_end - 500,
        )

        region = text[search_start:target_end]

        boundary_patterns = [
            r"\n\n",
            r"(?<=[.!?])\s+",
            r"\n",
        ]

        for pattern in boundary_patterns:
            matches = list(re.finditer(pattern, region))

            if matches:
                match = matches[-1]
                return search_start + match.end()

        return target_end

    @staticmethod
    def _move_to_word_boundary(text: str, position: int) -> int:
        while position < len(text) and not text[position].isspace():
            position += 1

        while position < len(text) and text[position].isspace():
            position += 1

        return position

    def _merge_small_final_chunk(
        self,
        chunks: list[str],
    ) -> list[str]:
        if len(chunks) < 2:
            return chunks

        last_chunk = chunks[-1]

        if len(last_chunk) >= self.minimum_chunk_size:
            return chunks

        previous = chunks[-2]

        if len(previous) + len(last_chunk) <= self.chunk_size + self.overlap:
            chunks[-2] = f"{previous}\n\n{last_chunk}"
            chunks.pop()

        return chunks