import re
from urllib.parse import urlparse
from ..models.investigation import InputType
from ..schemas.threat_object import ThreatObject, Indicator

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
IP_REGEX = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
HASH_REGEX = re.compile(r'\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{64}\b')

class IndicatorExtractor:
    @staticmethod
    def extract_urls(text: str) -> list[str]:
        url_pattern = re.compile(r'https?://(?:[a-zA-Z0-9-._~:/?#\[\]@!$&\'()*+,;=]|%[0-9a-fA-F]{2})+')
        return url_pattern.findall(text)
        
    @staticmethod
    def extract_domains(urls: list[str]) -> list[str]:
        domains = set()
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.hostname:
                    domains.add(parsed.hostname.lower())
            except Exception:
                pass
        return list(domains)

    @staticmethod
    def extract_emails(text: str) -> list[str]:
        return list(set(EMAIL_REGEX.findall(text)))

    @staticmethod
    def extract_ips(text: str) -> list[str]:
        return list(set(IP_REGEX.findall(text)))

    @staticmethod
    def extract_hashes(text: str) -> list[str]:
        return list(set(HASH_REGEX.findall(text)))

class UniversalInputProcessor:
    @staticmethod
    def process_input(input_type: InputType, raw_content: str) -> ThreatObject:
        normalized = raw_content.strip()
        
        urls = []
        if input_type in [InputType.URL, InputType.WEBPAGE]:
            urls = [normalized] if normalized.startswith(('http://', 'https://')) else [f"http://{normalized}"]
        else:
            urls = IndicatorExtractor.extract_urls(normalized)
            
        domains = IndicatorExtractor.extract_domains(urls)
        emails = IndicatorExtractor.extract_emails(normalized)
        ips = IndicatorExtractor.extract_ips(normalized)
        hashes = IndicatorExtractor.extract_hashes(normalized)
        
        indicators = []
        for url in urls:
            indicators.append(Indicator(type="URL", value=url))
        for d in domains:
            indicators.append(Indicator(type="DOMAIN", value=d))
        for em in emails:
            indicators.append(Indicator(type="EMAIL", value=em))
        for ip in ips:
            indicators.append(Indicator(type="IP", value=ip))
        for h in hashes:
            indicators.append(Indicator(type="HASH", value=h))
            
        return ThreatObject(
            input_type=input_type,
            raw_input_reference=normalized,
            normalized_text=normalized,
            urls=urls,
            domains=domains,
            extracted_indicators=indicators
        )
