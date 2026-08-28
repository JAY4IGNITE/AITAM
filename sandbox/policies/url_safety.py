import socket
import ipaddress
from urllib.parse import urlparse

class URLSafetyPolicy:
    @staticmethod
    def is_safe_to_analyze(url: str) -> bool:
        """
        Prevents SSRF by checking if a URL points to local, private, or cloud metadata endpoints.
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return False
                
            # Block explicit localhost
            if hostname in ["localhost", "127.0.0.1", "::1"]:
                return False
                
            # Block AWS/GCP/Azure metadata endpoints
            if hostname == "169.254.169.254":
                return False
                
            # Resolve IP and check if it's private
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                return False
                
            return True
        except Exception:
            return False
