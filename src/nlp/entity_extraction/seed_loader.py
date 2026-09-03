import json
from pathlib import Path

class SeedVocabularyLoader:
    def __init__(self, seed_dir: str = "data/seed") -> None:
        self.seed_dir = Path(seed_dir)

    def _load_json(self, filename: str):
        path = self.seed_dir / filename

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def load_companies(self) -> list[str]:
        data = self._load_json("companies.json")
        return [
            item["name"]
            for item in data
            if item.get("name")
        ]

    def load_facilities(self) -> list[str]:
        data = self._load_json("facilities.json")
        return [
            item["name"]
            for item in data
            if item.get("name")
        ]

    def load_locations(self) -> list[str]:
        data = self._load_json("locations.json")
        return [
            item["name"]
            for item in data
            if item.get("name")
        ]

    def load_countries(self) -> list[str]:
        data = self._load_json("countries.json")
        return [
            item["name"]
            for item in data
            if item.get("name")
        ]
    def load_products(self) -> list[str]:
        data = self._load_json("products.json")
        return [
            item["name"]
            for item in data
            if item.get("name")
        ]

    def load_materials(self) -> list[str]:
        data = self._load_json("materials.json")
        return [
            item["name"]
            for item in data
            if item.get("name")
        ]