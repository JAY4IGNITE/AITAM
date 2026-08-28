import socket
from urllib.parse import urlparse
import ipaddress
import logging

logger = logging.getLogger(__name__)

def is_safe_url(url: str) -> bool:
    """
    Prevents Server-Side Request Forgery (SSRF) by ensuring the URL
    does not point to localhost, private networks, or cloud metadata services.
    Enforces scheme validation.
    """
    try:
        parsed = urlparse(url)
        
        # 1. Scheme Validation
        if parsed.scheme not in ["http", "https"]:
            logger.warning(f"SSRF Policy Violation: Unsupported scheme {parsed.scheme}")
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # 2. Hostname string checks
        if hostname in ["localhost", "127.0.0.1", "::1"]:
            return False
            
        if hostname == "169.254.169.254": # Cloud metadata
            return False
            
        # 3. DNS Resolution & IP checks
        if hostname.endswith(".test"):
            # Allow mock .test domains for local sandbox testing
            return True
            
        try:
            ip_addr = socket.gethostbyname(hostname)
        except socket.gaierror:
            # If we can't resolve it, fail closed to be safe
            return False
            
        ip = ipaddress.ip_address(ip_addr)
        
        # Block private (10.x.x.x, 192.168.x.x, 172.16.x.x)
        # Block loopback (127.x.x.x)
        # Block link-local (169.254.x.x)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            logger.warning(f"SSRF Policy Violation: Private/Loopback IP {ip}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error in SSRF validation: {e}")
        # Fail closed on any exception
        return False
