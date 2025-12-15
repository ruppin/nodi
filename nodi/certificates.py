"""Certificate management for Nodi."""

from pathlib import Path
from typing import Optional, Tuple
from nodi.config.models import Certificates


class CertificateManager:
    """Manage SSL/TLS certificates."""

    def __init__(self):
        self.session_cert: Optional[Certificates] = None

    def get_cert_config(
        self, config_cert: Optional[Certificates], override_cert: Optional[Certificates] = None
    ) -> Optional[Tuple]:
        """
        Get certificate configuration for httpx.

        Priority:
        1. Override cert (from command line)
        2. Session cert (set in REPL)
        3. Config cert (from config file)

        Returns:
            Tuple of (cert_file, key_file) or None
        """
        cert = override_cert or self.session_cert or config_cert

        if not cert:
            return None

        # Expand paths
        cert = cert.expand_paths()

        if cert.cert and cert.key:
            return (cert.cert, cert.key)
        elif cert.cert:
            return cert.cert

        return None

    def get_ca_bundle(
        self, config_cert: Optional[Certificates], override_cert: Optional[Certificates] = None
    ) -> Optional[str]:
        """Get CA bundle path."""
        cert = override_cert or self.session_cert or config_cert

        if not cert:
            return None

        # Expand paths
        cert = cert.expand_paths()

        return cert.ca if cert.ca else None

    def get_verify_mode(
        self, config_cert: Optional[Certificates], override_cert: Optional[Certificates] = None
    ) -> bool:
        """Get SSL verification mode."""
        cert = override_cert or self.session_cert or config_cert

        if not cert:
            return True

        return cert.verify

    def set_session_cert(self, cert: Certificates):
        """Set session-wide certificate."""
        self.session_cert = cert

    def clear_session_cert(self):
        """Clear session certificate."""
        self.session_cert = None

    def validate_cert_files(self, cert: Certificates) -> Tuple[bool, list[str]]:
        """
        Validate certificate files exist.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        cert = cert.expand_paths()

        if cert.cert:
            cert_path = Path(cert.cert)
            if not cert_path.exists():
                errors.append(f"Certificate file not found: {cert.cert}")
            elif not cert_path.is_file():
                errors.append(f"Certificate path is not a file: {cert.cert}")

        if cert.key:
            key_path = Path(cert.key)
            if not key_path.exists():
                errors.append(f"Key file not found: {cert.key}")
            elif not key_path.is_file():
                errors.append(f"Key path is not a file: {cert.key}")

        if cert.ca:
            ca_path = Path(cert.ca)
            if not ca_path.exists():
                errors.append(f"CA bundle file not found: {cert.ca}")
            elif not ca_path.is_file():
                errors.append(f"CA bundle path is not a file: {cert.ca}")

        return len(errors) == 0, errors
