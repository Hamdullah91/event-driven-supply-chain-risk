from __future__ import annotations

import json
from pathlib import Path

from .models import ProcessedFiling


class ProcessedFilingExporter:
    def save_json(
        self,
        filing: ProcessedFiling,
        output_path: str | Path,
    ) -> Path:
        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                filing.to_dict(),
                file,
                indent=2,
                ensure_ascii=False,
            )

        return path