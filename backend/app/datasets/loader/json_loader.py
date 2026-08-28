import json
from typing import Iterator

def load_json(filepath: str) -> Iterator[dict]:
    """Loads a JSON or JSONL file and yields records."""
    if filepath.endswith(".jsonl"):
        with open(filepath, mode="r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
    else:
        with open(filepath, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
            elif isinstance(data, dict) and "data" in data:
                for item in data["data"]:
                    yield item
            else:
                yield data
