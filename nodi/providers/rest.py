"""REST/HTTP provider for Nodi."""

import time
from typing import Dict, Optional, Any
import httpx

from nodi.providers.base import DataProvider, ProviderRequest, ProviderResponse
from nodi.config.models import Certificates


class RestProvider(DataProvider):
    """REST/HTTP provider using httpx."""

    def __init__(self, name: str = "rest", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.client: Optional[httpx.Client] = None
        self._setup_client()

    def _setup_client(self):
        """Setup httpx client with configuration."""
        client_config = {
            "timeout": self.config.get("timeout", 30),
            "follow_redirects": self.config.get("follow_redirects", True),
            "http2": self.config.get("http2", False),  # HTTP/2 disabled by default
        }

        # SSL/TLS configuration
        verify = self.config.get("verify_ssl", True)
        cert = self.config.get("cert")

        if cert:
            # If cert is provided as a tuple (cert_file, key_file)
            if isinstance(cert, (list, tuple)) and len(cert) == 2:
                client_config["cert"] = cert
            # If cert is a string path
            elif isinstance(cert, str):
                key = self.config.get("key")
                if key:
                    client_config["cert"] = (cert, key)
                else:
                    client_config["cert"] = cert

        client_config["verify"] = verify

        self.client = httpx.Client(**client_config)

    def request(self, request: ProviderRequest, certificates: Optional[Certificates] = None) -> ProviderResponse:
        """
        Execute HTTP request.

        Args:
            request: ProviderRequest with HTTP details
            certificates: Optional SSL certificates for this request

        Returns:
            ProviderResponse with HTTP result
        """
        # Update certificates if provided for this request
        if certificates:
            self.update_certificates(certificates)
        elif not self.client:
            self._setup_client()

        start_time = time.time()

        try:
            response = self.client.request(
                method=request.method,
                url=request.resource,
                headers=request.headers,
                params=request.params,
                json=request.data if isinstance(request.data, dict) else None,
                content=request.data if isinstance(request.data, (str, bytes)) else None,
                timeout=request.timeout or self.config.get("timeout", 30),
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Parse response data
            data = self._parse_response_data(response)

            return ProviderResponse(
                status_code=response.status_code,
                data=data,
                headers=dict(response.headers),
                elapsed_time=elapsed_ms,
                metadata={
                    "method": request.method,
                    "url": request.resource,
                    "http_version": response.http_version,
                    "reason_phrase": response.reason_phrase,
                },
            )

        except httpx.TimeoutException as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return ProviderResponse(
                status_code=408,
                data=None,
                error=f"Request timeout: {str(e)}",
                elapsed_time=elapsed_ms,
            )

        except httpx.ConnectError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return ProviderResponse(
                status_code=503,
                data=None,
                error=f"Connection error: {str(e)}",
                elapsed_time=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return ProviderResponse(
                status_code=500,
                data=None,
                error=f"Request failed: {str(e)}",
                elapsed_time=elapsed_ms,
            )

    def _parse_response_data(self, response: httpx.Response) -> Any:
        """Parse response data based on content type."""
        content_type = response.headers.get("content-type", "")

        # JSON
        if "application/json" in content_type:
            try:
                return response.json()
            except Exception:
                return response.text

        # XML
        elif "application/xml" in content_type or "text/xml" in content_type:
            return response.text

        # HTML
        elif "text/html" in content_type:
            return response.text

        # Text
        elif "text/" in content_type:
            return response.text

        # Binary
        else:
            # Return bytes for binary content
            return response.content

    def test_connection(self) -> bool:
        """Test HTTP connectivity."""
        try:
            # Try a simple HEAD request to a test URL if provided
            test_url = self.config.get("test_url", "https://www.google.com")
            response = self.client.head(test_url, timeout=5)
            return response.status_code < 500
        except Exception:
            return False

    def close(self):
        """Close HTTP client."""
        if self.client:
            self.client.close()
            self.client = None

    def update_certificates(self, certificates: Optional[Certificates]):
        """Update SSL certificates and recreate client."""
        if certificates:
            from pathlib import Path

            # Expand paths for tilde and relative paths
            expanded_certs = certificates.expand_paths()

            # Set client certificate and key
            if expanded_certs.cert and expanded_certs.key:
                # Only set if files exist
                cert_path = Path(expanded_certs.cert)
                key_path = Path(expanded_certs.key)
                if cert_path.exists() and key_path.exists():
                    self.config["cert"] = expanded_certs.cert
                    self.config["key"] = expanded_certs.key
                else:
                    # Files don't exist, skip cert config
                    self.config.pop("cert", None)
                    self.config.pop("key", None)
            elif expanded_certs.cert:
                # Just cert file (for some cases)
                cert_path = Path(expanded_certs.cert)
                if cert_path.exists():
                    self.config["cert"] = expanded_certs.cert
                else:
                    self.config.pop("cert", None)

            # Set CA certificate for verification
            if expanded_certs.ca:
                ca_path = Path(expanded_certs.ca)
                if ca_path.exists():
                    # httpx uses 'verify' parameter for CA bundle path
                    self.config["verify_ssl"] = expanded_certs.ca
                else:
                    # CA file doesn't exist, use default verification
                    self.config["verify_ssl"] = expanded_certs.verify
            else:
                # No CA specified, use verify flag
                self.config["verify_ssl"] = expanded_certs.verify

        # Recreate client with new config
        self.close()
        self._setup_client()

    def get_client_info(self) -> Dict[str, Any]:
        """Get HTTP client information."""
        return {
            "http2_enabled": self.config.get("http2", True),
            "timeout": self.config.get("timeout", 30),
            "follow_redirects": self.config.get("follow_redirects", True),
            "verify_ssl": self.config.get("verify_ssl", True),
        }

    def _get_headers(
        self,
        alias_config: dict[str, Any],
        request_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Get headers for the request with case-insensitive merge.

        Merge order (later wins):
        1. environment headers
        2. alias headers
        3. request headers

        Args:
            alias_config: Alias configuration
            request_headers: Optional per-request headers (highest priority)

        Returns:
            Merged headers dict
        """
        # start with environment headers
        headers = self.env_headers.copy()

        # merge alias-level headers (case-insensitive)
        alias_headers = alias_config.get("headers", {})
        for k, v in alias_headers.items():
            # find existing key (case-insensitive) and replace
            existing_key = next((h for h in headers if h.lower() == k.lower()), None)
            if existing_key:
                del headers[existing_key]
            headers[k] = v

        # merge request-level headers (case-insensitive, highest priority)
        if request_headers:
            for k, v in request_headers.items():
                existing_key = next((h for h in headers if h.lower() == k.lower()), None)
                if existing_key:
                    del headers[existing_key]
                headers[k] = v

        return headers

    def _make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        request_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with merged headers.

        Args:
            method: HTTP method
            url: Request URL
            headers: Base headers (from config)
            params: Query parameters
            json_data: JSON body
            request_headers: Optional per-request header overrides

        Returns:
            Response dict with status_code, headers, and data
        """
        # merge request-level headers (they override base headers)
        final_headers = headers.copy()
        if request_headers:
            for k, v in request_headers.items():
                existing_key = next((h for h in final_headers if h.lower() == k.lower()), None)
                if existing_key:
                    del final_headers[existing_key]
                final_headers[k] = v

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=final_headers,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json() if response.content else None,
            }
        except requests.exceptions.Timeout:
            msg = f"Request timed out after {self.timeout}s"
            raise TimeoutError(msg)
        except requests.exceptions.RequestException as e:
            msg = f"Request failed: {e!s}"
            raise RuntimeError(msg) from e

    def make_request(
        self,
        alias: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a request using alias with optional header overrides.
        
        Args:
            alias: Alias name from config
            params: Optional query/body parameters
            headers: Optional runtime headers (merged with config headers)
        """
        alias_config = self.config.get_alias(alias)
        if not alias_config:
            msg = f"Alias '{alias}' not found"
            raise ValueError(msg)

        method = alias_config.get("method", "GET").upper()
        path = alias_config.get("path", "")
        
        if params and "{" in path:
            path = path.format(**params)
        
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

        # Merge headers: env -> alias -> runtime (runtime wins)
        merged_headers = self.env_headers.copy()
        merged_headers.update(alias_config.get("headers", {}))
        if headers:
            merged_headers.update(headers)
        
        query_params = None
        json_data = None
        
        if method in {"POST", "PUT", "PATCH"} and params:
            json_data = params
        elif params:
            query_params = params
        
        return self._make_request(method, url, merged_headers, query_params, json_data)
