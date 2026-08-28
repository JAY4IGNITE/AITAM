import re
from urllib.parse import urlparse
from ..models.investigation import InputType
from ..schemas.threat_object import ThreatObject, Indicator

class IndicatorExtractor:
    @staticmethod
    def extract_urls(text: str) -> list[str]:
        # Basic URL extraction regex
        url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*')
        return url_pattern.findall(text)
        
    @staticmethod
    def extract_domains(urls: list[str]) -> list[str]:
        domains = set()
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.netloc:
                    domains.add(parsed.netloc.lower())
            except:
                pass
        return list(domains)

class UniversalInputProcessor:
    @staticmethod
    def process_input(input_type: InputType, raw_content: str) -> ThreatObject:
        normalized = raw_content.strip()
        
        urls = []
        
        if input_type == InputType.URL or input_type == InputType.WEBPAGE:
            urls = [normalized] if normalized.startswith('http') else [f"http://{normalized}"]
        else:
            urls = IndicatorExtractor.extract_urls(normalized)
            
        domains = IndicatorExtractor.extract_domains(urls)
        
        indicators = []
        for url in urls:
            indicators.append(Indicator(type="URL", value=url))
        for d in domains:
            indicators.append(Indicator(type="DOMAIN", value=d))
            
        return ThreatObject(
            input_type=input_type,
            raw_input_reference=normalized,
            normalized_text=normalized,
            urls=urls,
            domains=domains,
            extracted_indicators=indicators
        )
