import socket
from urllib.parse import urlparse
import ipaddress

def is_safe_url(url: str) -> bool:
    """
    Prevents Server-Side Request Forgery (SSRF) by ensuring the URL
    does not point to localhost, private networks, or cloud metadata services.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
            
        if hostname in ["localhost", "127.0.0.1", "::1"]:
            return False
            
        if hostname == "169.254.169.254":
            return False
            
        # Resolve to IP
        ip_addr = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_addr)
        
        # Block private, loopback, and metadata IPs
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
            
        return True
    except Exception:
        # If we can't resolve it, it's safer to block it in the sandbox
        return False
