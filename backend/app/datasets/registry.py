import os
import uuid
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.dataset import Dataset, DatasetSample
from .loader.csv_loader import load_csv
from .loader.json_loader import load_json
from .normalizer.universal import normalize_sample
from .validators.schema import DatasetValidator

class DatasetRegistry:
    @staticmethod
    async def import_dataset(
        session: AsyncSession, 
        file_path: str, 
        name: str, 
        source: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        """
        Parses a file, validates/normalizes it, and saves it to the database.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name=name,
            source=source,
            description=description,
            data_type=file_path.split(".")[-1].lower()
        )
        session.add(dataset)
        await session.commit()
        
        # Determine loader
        if file_path.endswith(".csv"):
            iterator = load_csv(file_path)
        elif file_path.endswith(".json") or file_path.endswith(".jsonl"):
            iterator = load_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
            
        validator = DatasetValidator()
        samples_to_insert = []
        valid_count = 0
        skip_count = 0
        
        for raw_sample in iterator:
            try:
                content, input_type, label = normalize_sample(raw_sample)
                if validator.validate(content, raw_sample):
                    sample = DatasetSample(
                        id=str(uuid.uuid4()),
                        dataset_id=dataset.id,
                        input_type=input_type,
                        content=content,
                        label=label,
                        metadata_payload=raw_sample
                    )
                    samples_to_insert.append(sample)
                    valid_count += 1
                else:
                    skip_count += 1
            except Exception:
                skip_count += 1
                
            # Batch insert
            if len(samples_to_insert) >= 1000:
                session.add_all(samples_to_insert)
                await session.commit()
                samples_to_insert = []
                
        if samples_to_insert:
            session.add_all(samples_to_insert)
            await session.commit()
            
        return {
            "dataset_id": dataset.id,
            "imported": valid_count,
            "skipped": skip_count
        }
