"""Validators for Nodi."""

import re
from typing import Tuple


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"

    if not url.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"

    # Basic URL validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        return False, "Invalid URL format"

    return True, ""


def validate_http_method(method: str) -> Tuple[bool, str]:
    """
    Validate HTTP method.

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

    method = method.upper()
    if method not in valid_methods:
        return False, f"Invalid HTTP method. Must be one of: {', '.join(valid_methods)}"

    return True, ""


def validate_service_name(name: str) -> Tuple[bool, str]:
    """
    Validate service name.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Service name cannot be empty"

    # Allow alphanumeric, hyphens, underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return False, "Service name can only contain letters, numbers, hyphens, and underscores"

    return True, ""


def validate_environment_name(name: str) -> Tuple[bool, str]:
    """
    Validate environment name.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Environment name cannot be empty"

    # Allow alphanumeric, hyphens, underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return (
            False,
            "Environment name can only contain letters, numbers, hyphens, and underscores",
        )

    return True, ""
