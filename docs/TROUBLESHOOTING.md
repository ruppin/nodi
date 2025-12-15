# Troubleshooting Guide

Common issues and solutions for Nodi installation and usage.

## Installation Issues

### pyjq Installation Fails on Windows

**Error**: `Failed building wheel for pyjq`

**Cause**: `pyjq` requires C compilation and has dependencies that are difficult to build on Windows.

**Solution**: Skip pyjq installation - Nodi works fine without it!

```bash
# Install without pyjq (recommended for Windows)
pip install -e .

# This installs all required dependencies except pyjq
```

**Impact**: You'll use Nodi's built-in simple filtering instead of full jq support. The following filters work without pyjq:
- `.field` - Get field value
- `.[n]` - Array index access
- `.[]` - Iterate array
- `.a.b.c` - Nested field access
- `length` - Get length
- `keys` - Get keys
- `values` - Get values
- `type` - Get type

**If you need full jq support**:
1. Install WSL (Windows Subsystem for Linux)
2. Install Nodi in WSL where pyjq builds successfully
3. Or use an alternative like `jq` command line tool separately

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```bash
# Reinstall all dependencies
pip install -e .

# Or install specific missing package
pip install package-name
```

### Permission Errors

**Error**: `PermissionError` or `Access denied`

**Solution**:
```bash
# Use --user flag
pip install --user -e .

# Or use virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e .
```

## Configuration Issues

### Config File Not Found

**Error**: No configuration found

**Solution**:
```bash
# Initialize configuration
nodi init

# This creates ~/.nodi/config.yml
```

### Configuration Validation Failed

**Error**: Configuration validation errors

**Solution**:
```bash
# Validate and see errors
nodi validate

# Common issues:
# - Invalid URLs (must start with http:// or https://)
# - Missing base_url for environments
# - Invalid default_service or default_environment
```

### Environment Variables Not Working

**Problem**: Headers show `${VAR_NAME}` instead of actual values

**Solution**:
1. Create `.env` file in your project directory:
   ```
   DEV_API_KEY=your-actual-key
   QA_API_KEY=your-actual-key
   ```

2. Or set environment variables:
   ```bash
   # Windows
   set DEV_API_KEY=your-actual-key

   # Unix/macOS
   export DEV_API_KEY=your-actual-key
   ```

## Runtime Issues

### Connection Refused / Network Errors

**Error**: `Connection error` or `503`

**Possible Causes**:
1. Service is down
2. Wrong URL in configuration
3. Network/firewall issues
4. SSL certificate issues

**Solutions**:
```bash
# Check URL in config
nodi services

# Test connection
curl https://your-service-url/health

# Disable SSL verification (for testing only!)
# In config.yml:
services:
  my-service:
    dev:
      verify_ssl: false
```

### SSL Certificate Errors

**Error**: SSL verification failed

**Solutions**:

1. **Add CA certificate**:
   ```yaml
   certificates:
     dev:
       ca: ~/.certs/ca-bundle.crt
   ```

2. **Disable verification (dev only)**:
   ```yaml
   certificates:
     dev:
       verify: false
   ```

3. **Use proper certificates**:
   ```yaml
   certificates:
     prod:
       cert: ~/.certs/client.crt
       key: ~/.certs/client.key
       ca: ~/.certs/ca.crt
   ```

### REPL Not Starting

**Error**: REPL crashes or doesn't start

**Solutions**:
```bash
# Check if nodi command exists
which nodi  # Unix
where nodi  # Windows

# Run directly
python -m nodi

# Check for errors
python -m nodi --help
```

### Import Errors

**Error**: `ImportError` or `ModuleNotFoundError`

**Solution**:
```bash
# Verify installation
python verify_install.py

# Reinstall
pip uninstall nodi
pip install -e .
```

## Usage Issues

### Service Not Found

**Error**: `Service not found: xxx`

**Solutions**:
```bash
# List available services
nodi services

# Check service name spelling
# Check if service is defined in config

# Use service alias if configured
# Instead of: long-service-name
# Use: short-alias
```

### Endpoint Resolution Fails

**Error**: `Invalid request format` or `Endpoint not found`

**Solutions**:
```bash
# Check syntax
nodi request service.env@endpoint

# Examples of correct syntax:
user-service.dev@users
user-service.dev@user:123
order-service.qa@orders?page=2

# Check aliases in config
nodi> service user-service  # Shows service info including aliases
```

### Filter Errors

**Error**: Filter not working or `Filter 'xxx' not supported`

**Cause**: Using advanced jq syntax without pyjq installed

**Solutions**:
1. Use simple built-in filters:
   ```bash
   users | jq length
   user:1 | jq .name
   users | jq .[0]
   ```

2. Or install pyjq (if possible on your platform):
   ```bash
   pip install pyjq
   ```

### Output Not Formatted

**Problem**: JSON not colored or formatted

**Solutions**:
```bash
# Check output format
nodi> format json

# Try different formatter
nodi> format table
nodi> format yaml

# For CLI
nodi request service.env@endpoint --format json
```

## Performance Issues

### Slow Requests

**Problem**: Requests take too long

**Solutions**:

1. **Increase timeout**:
   ```yaml
   services:
     my-service:
       dev:
         timeout: 60  # seconds
   ```

2. **Check network**:
   ```bash
   # Test directly
   curl -w "@-" https://your-service/endpoint
   ```

3. **Use verbose mode**:
   ```bash
   nodi request service.dev@endpoint --verbose
   ```

## Windows-Specific Issues

### Command Not Found (Windows)

**Error**: `'nodi' is not recognized`

**Solutions**:
```bash
# Add Python Scripts to PATH
# Or use python -m
python -m nodi

# Or use full path
%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts\nodi.exe
```

### Path Issues

**Problem**: Config file or certificate paths not working

**Solution**: Use Windows paths with escaped backslashes or forward slashes:
```yaml
# Option 1: Forward slashes (recommended)
certificates:
  dev:
    cert: C:/Users/YourName/.certs/cert.crt

# Option 2: Escaped backslashes
cert: C:\\Users\\YourName\\.certs\\cert.crt

# Option 3: Raw strings with ~
cert: ~/.certs/cert.crt  # Expands to C:\Users\YourName\.certs\cert.crt
```

## Getting More Help

### Enable Debug Logging

Create a file `debug_nodi.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from nodi.cli import main
main()
```

Run it:
```bash
python debug_nodi.py
```

### Check Version

```bash
nodi --version
python --version
pip list | grep nodi
```

### Verify Installation

```bash
python verify_install.py
```

### Report Issues

If you've tried everything above, please report the issue:

1. Check existing issues: https://github.com/yourusername/nodi/issues
2. Create new issue with:
   - Python version
   - Operating system
   - Full error message
   - Steps to reproduce
   - Output of `python verify_install.py`

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| pyjq won't install | Skip it: `pip install -e .` |
| Config not found | Run: `nodi init` |
| Service not found | Check: `nodi services` |
| SSL errors | Set `verify: false` in config (dev only) |
| Import errors | Run: `python verify_install.py` |
| Slow requests | Increase `timeout` in config |
| Headers not working | Check `.env` file exists |
| Command not found | Use: `python -m nodi` |

## Still Need Help?

- Read the [README.md](README.md)
- Check [QUICKSTART.md](QUICKSTART.md)
- Review [DEVELOPMENT.md](DEVELOPMENT.md)
- Open an issue on GitHub
