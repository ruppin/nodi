#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script for Nodi installation.
Run this after installing to verify everything works.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def verify_imports():
    """Verify all imports work."""
    print("Verifying imports...")
    errors = []

    try:
        import nodi
        print(f"  ✓ nodi package (version {nodi.__version__})")
    except ImportError as e:
        errors.append(f"  ✗ Failed to import nodi: {e}")

    try:
        from nodi.config.models import Config
        print("  ✓ nodi.config.models")
    except ImportError as e:
        errors.append(f"  ✗ Failed to import config.models: {e}")

    try:
        from nodi.config.loader import ConfigLoader
        print("  ✓ nodi.config.loader")
    except ImportError as e:
        errors.append(f"  ✗ Failed to import config.loader: {e}")

    try:
        from nodi.environment.manager import EnvironmentManager
        print("  ✓ nodi.environment.manager")
    except ImportError as e:
        errors.append(f"  ✗ Failed to import environment.manager: {e}")

    try:
        from nodi.providers.rest import RestProvider
        print("  ✓ nodi.providers.rest")
    except ImportError as e:
        errors.append(f"  ✗ Failed to import providers.rest: {e}")

    try:
        from nodi.repl import NodiREPL
        print("  ✓ nodi.repl")
    except ImportError as e:
        errors.append(f"  ✗ Failed to import repl: {e}")

    try:
        from nodi.cli import cli
        print("  ✓ nodi.cli")
    except ImportError as e:
        errors.append(f"  ✗ Failed to import cli: {e}")

    return errors


def verify_dependencies():
    """Verify required dependencies are installed."""
    print("\nVerifying dependencies...")
    errors = []

    dependencies = [
        "httpx",
        "yaml",
        "dotenv",
        "prompt_toolkit",
        "pygments",
        "rich",
        "tabulate",
        "click",
    ]

    for dep in dependencies:
        try:
            if dep == "yaml":
                import yaml
            elif dep == "dotenv":
                import dotenv
            else:
                __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            errors.append(f"  ✗ Missing dependency: {dep}")

    return errors


def verify_config_creation():
    """Verify config can be created."""
    print("\nVerifying config creation...")
    errors = []

    try:
        from nodi.config.models import Config, Service, ServiceEnvironment

        env = ServiceEnvironment(base_url="https://api.example.com")
        service = Service(name="test", environments={"dev": env})
        config = Config(services={"test": service})

        print("  ✓ Config objects can be created")
    except Exception as e:
        errors.append(f"  ✗ Failed to create config: {e}")

    return errors


def verify_url_resolution():
    """Verify URL resolution works."""
    print("\nVerifying URL resolution...")
    errors = []

    try:
        from nodi.config.models import Config, Service, ServiceEnvironment
        from nodi.environment.resolver import URLResolver

        env = ServiceEnvironment(base_url="https://api.example.com")
        service = Service(
            name="test", environments={"dev": env}, aliases={"users": "/api/v1/users"}
        )
        config = Config(services={"test": service})

        resolver = URLResolver(config)
        spec = resolver.parse("test.dev@users", default_service="test", default_env="dev")
        url = resolver.resolve(spec)

        if url == "https://api.example.com/api/v1/users":
            print("  ✓ URL resolution works")
        else:
            errors.append(f"  ✗ URL resolution incorrect: got {url}")
    except Exception as e:
        errors.append(f"  ✗ Failed URL resolution: {e}")

    return errors


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Nodi Installation Verification")
    print("=" * 60)

    all_errors = []

    all_errors.extend(verify_imports())
    all_errors.extend(verify_dependencies())
    all_errors.extend(verify_config_creation())
    all_errors.extend(verify_url_resolution())

    print("\n" + "=" * 60)
    if all_errors:
        print("VERIFICATION FAILED")
        print("=" * 60)
        print("\nErrors found:")
        for error in all_errors:
            print(error)
        print(
            "\nPlease install missing dependencies:"
            "\n  pip install -e ."
            "\n  or"
            "\n  pip install -e .[full]"
        )
        sys.exit(1)
    else:
        print("✓ ALL CHECKS PASSED")
        print("=" * 60)
        print("\nNodi is installed correctly!")
        print("\nNext steps:")
        print("  1. Initialize config: nodi init")
        print("  2. Edit config: ~/.nodi/config.yml")
        print("  3. Start using: nodi")
        print("\nFor help: nodi --help")
        sys.exit(0)


if __name__ == "__main__":
    main()
