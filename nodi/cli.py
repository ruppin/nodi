"""Command-line interface for Nodi."""

import click
import sys
import os
from pathlib import Path
from typing import Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from nodi.config.loader import ConfigLoader
from nodi.config.validator import ConfigValidator
from nodi.repl import NodiREPL
from nodi.environment.manager import EnvironmentManager
from nodi.providers.rest import RestProvider
from nodi.providers.base import ProviderRequest
from nodi.formatters.json import JSONFormatter
from nodi.formatters.yaml_fmt import YAMLFormatter
from nodi.formatters.table import TableFormatter
from nodi.formatters.csv_fmt import CSVFormatter
from nodi.utils.color import Color
from nodi.history import HistoryManager
from nodi.filters import JSONFilter


@click.group(invoke_without_command=True)
@click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.pass_context
def cli(ctx, config, version):
    """Nodi - Interactive Data Query Tool for Microservices."""
    if version:
        from nodi import __version__

        click.echo(f"nodi version {__version__}")
        sys.exit(0)

    # Store config path in context
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@cli.command()
@click.pass_context
def repl(ctx):
    """Start interactive REPL mode."""
    config_path = ctx.obj.get("config_path")

    # Load config
    loader = ConfigLoader()
    config = loader.load(config_path)

    # Validate config
    validator = ConfigValidator()
    if not validator.validate(config):
        click.echo(Color.error("Configuration validation failed:"))
        for error in validator.get_errors():
            click.echo(f"  ✗ {error}")
        sys.exit(1)

    if validator.get_warnings():
        click.echo(Color.warning("Configuration warnings:"))
        for warning in validator.get_warnings():
            click.echo(f"  ⚠ {warning}")
        click.echo()

    # Start REPL
    repl_instance = NodiREPL(config)
    repl_instance.run()


@cli.command()
@click.argument("request_spec", required=False)
@click.option("--method", "-X", default="GET", help="HTTP method")
@click.option("--data", "-d", help="Request data (JSON)")
@click.option("--header", "-H", multiple=True, help="Additional headers")
@click.option("--format", "-f", type=click.Choice(["json", "yaml", "table", "csv"]), default="json")
@click.option("--filter", help="jq filter expression")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.pass_context
def request(ctx, request_spec, method, data, header, format, filter, verbose):
    """Execute a single HTTP request."""
    if not request_spec:
        click.echo("Usage: nodi request <service.env@endpoint>")
        click.echo("Example: nodi request user-service.dev@users")
        sys.exit(1)

    config_path = ctx.obj.get("config_path")

    # Load config
    loader = ConfigLoader()
    config = loader.load(config_path)

    # Validate config
    validator = ConfigValidator()
    if not validator.validate(config):
        click.echo(Color.error("Configuration validation failed"))
        sys.exit(1)

    # Setup
    env_manager = EnvironmentManager(config)
    rest_provider = RestProvider()
    history = HistoryManager()

    try:
        # Parse request spec
        spec, url = env_manager.resolve_url(request_spec)

        # Get headers
        headers = env_manager.get_headers(spec.service, spec.environment)

        # Add additional headers
        for h in header:
            if ":" in h:
                name, value = h.split(":", 1)
                headers[name.strip()] = value.strip()

        # Get certificates for the environment
        certificates = env_manager.get_certificates(spec.environment)

        if verbose:
            click.echo(f"{method} {url}")
            click.echo(f"Headers: {headers}")
            if certificates:
                click.echo(f"Certificates configured: cert={certificates.cert}, key={certificates.key}, ca={certificates.ca}")
            click.echo()

        # Create and execute request
        request_obj = ProviderRequest(method=method, resource=url, headers=headers, data=data)

        response = rest_provider.request(request_obj, certificates=certificates)

        # Add to history
        history.add(
            method=method,
            service=spec.service,
            environment=spec.environment,
            url=url,
            status_code=response.status_code,
            elapsed_ms=response.elapsed_time or 0,
        )

        # Apply filter if specified
        output_data = response.data
        if filter and output_data:
            json_filter = JSONFilter()
            output_data = json_filter.apply(output_data, filter)

        # Format output
        if format == "json":
            formatter = JSONFormatter()
            click.echo(formatter.format(output_data))
        elif format == "yaml":
            formatter = YAMLFormatter()
            click.echo(formatter.format(output_data))
        elif format == "table":
            formatter = TableFormatter()
            click.echo(formatter.format(output_data))
        elif format == "csv":
            formatter = CSVFormatter()
            click.echo(formatter.format(output_data))

        # Exit with appropriate code
        if response.is_success:
            sys.exit(0)
        elif response.status_code >= 400 and response.status_code < 500:
            sys.exit(1)
        elif response.status_code >= 500:
            sys.exit(2)
        else:
            sys.exit(3)

    except Exception as e:
        click.echo(Color.error(f"Request failed: {str(e)}"))
        sys.exit(4)


@cli.command()
@click.pass_context
def services(ctx):
    """List all configured services."""
    config_path = ctx.obj.get("config_path")

    loader = ConfigLoader()
    config = loader.load(config_path)

    click.echo(Color.bold("Available services:"))
    for service_name, service in config.services.items():
        envs = ", ".join(service.environments.keys())
        click.echo(f"  {Color.info(service_name):30s} → {envs}")
        if service.description:
            click.echo(f"    {service.description}")


@cli.command()
@click.argument("service_name", required=False)
@click.pass_context
def envs(ctx, service_name):
    """List environments for a service or all environments."""
    config_path = ctx.obj.get("config_path")

    loader = ConfigLoader()
    config = loader.load(config_path)

    if service_name:
        service = config.get_service(service_name)
        if not service:
            click.echo(Color.error(f"Service not found: {service_name}"))
            sys.exit(1)

        click.echo(Color.bold(f"Environments for {service_name}:"))
        for env_name in service.environments.keys():
            click.echo(f"  {env_name}")
    else:
        all_envs = config.list_environments()
        click.echo(Color.bold("All environments:"))
        for env in all_envs:
            click.echo(f"  {env}")


@cli.command()
def init():
    """Initialize Nodi configuration."""
    config_dir = Path.home() / ".nodi"
    config_file = config_dir / "config.yml"

    if config_file.exists():
        click.echo(f"Configuration already exists at {config_file}")
        if not click.confirm("Overwrite?"):
            sys.exit(0)

    loader = ConfigLoader()
    created_path = loader.create_default_config(config_file)

    click.echo(Color.success(f"Created configuration at {created_path}"))
    click.echo("\nEdit the configuration file to add your services and environments.")
    click.echo(f"  {created_path}")


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate configuration file."""
    config_path = ctx.obj.get("config_path")

    loader = ConfigLoader()
    config = loader.load(config_path)

    validator = ConfigValidator()
    is_valid = validator.validate(config)

    validator.print_report()

    sys.exit(0 if is_valid else 1)


def main():
    """Main entry point."""
    # If no arguments, start REPL
    if len(sys.argv) == 1:
        sys.argv.append("repl")

    cli(obj={})


if __name__ == "__main__":
    main()
