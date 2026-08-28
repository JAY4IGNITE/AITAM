from typing import List, Dict, Any

class DatasetValidator:
    def __init__(self):
        self.seen_content = set()
        
    def validate(self, content: str, raw_sample: Dict[str, Any]) -> bool:
        """
        Returns True if sample is valid, False if it should be skipped.
        Checks for empty content, oversized content, and duplicates.
        """
        if not content:
            return False
            
        # Oversized record check (e.g. > 100KB)
        if len(content.encode('utf-8')) > 100 * 1024:
            return False
            
        # Deduplication
        content_hash = hash(content)
        if content_hash in self.seen_content:
            return False
            
        self.seen_content.add(content_hash)
        return True
