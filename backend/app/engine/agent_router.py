from ..models.investigation import InputType

# Dynamic imports to avoid circular dependencies
def get_agents_for_input(input_type: InputType) -> list:
    from ..agents.url_agent import URLIntelligenceAgent
    from ..agents.content_agent import ContentIntelligenceAgent
    from ..agents.brand_agent import BrandImpersonationAgent
    from ..agents.threat_intel import ThreatIntelligenceAgent
    from ..agents.phishing_agent import PhishingDetectionAgent
    from ..agents.email_agent import EmailIntelligenceAgent
    from ..agents.attachment_agent import AttachmentAnalysisAgent
    from ..agents.sms_agent import SMSIntelligenceAgent
    from ..agents.social_agent import SocialMessageIntelligenceAgent
    from ..agents.qr_processor import QRCodeProcessor
    
    routes = {
        InputType.URL: [URLIntelligenceAgent, BrandImpersonationAgent, ThreatIntelligenceAgent, PhishingDetectionAgent],
        InputType.EMAIL: [EmailIntelligenceAgent, AttachmentAnalysisAgent, ContentIntelligenceAgent, URLIntelligenceAgent, BrandImpersonationAgent, ThreatIntelligenceAgent, PhishingDetectionAgent],
        InputType.SMS: [SMSIntelligenceAgent, ContentIntelligenceAgent, URLIntelligenceAgent, BrandImpersonationAgent, ThreatIntelligenceAgent, PhishingDetectionAgent],
        InputType.QR: [QRCodeProcessor, URLIntelligenceAgent, BrandImpersonationAgent, ThreatIntelligenceAgent, PhishingDetectionAgent],
        InputType.WEBPAGE: [URLIntelligenceAgent, ThreatIntelligenceAgent], # Sandbox is handled implicitly via Orchestrator risk
        InputType.SOCIAL: [SocialMessageIntelligenceAgent, ContentIntelligenceAgent, URLIntelligenceAgent, BrandImpersonationAgent, ThreatIntelligenceAgent, PhishingDetectionAgent]
    }
    
    return routes.get(input_type, [])

class AgentRouter:
    @staticmethod
    def get_route(input_type: InputType):
        return get_agents_for_input(input_type)
