import csv
from typing import Iterator

def load_csv(filepath: str) -> Iterator[dict]:
    """Loads a CSV file and yields rows as dictionaries."""
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row
