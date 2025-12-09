"""
Config command - Configuration management.
"""

import click
from pathlib import Path
import os

from transmute.cli.ui import (
    print_header, print_success, print_error, print_info,
    console
)


@click.group()
def config():
    """
    Configuration management.
    
    Initialize and manage Transmute configuration.
    """
    pass


@config.command('init')
@click.option(
    '--force',
    is_flag=True,
    help='Overwrite existing configuration'
)
def init_config(force):
    """
    Initialize Transmute configuration.
    
    Creates .env file with required settings.
    
    Examples:
    
        transmute config init
        transmute config init --force
    """
    print_header("⚙️ Configuration Setup")
    
    env_file = Path(".env")
    
    if env_file.exists() and not force:
        print_error(".env file already exists. Use --force to overwrite.")
        return
    
    # Create .env template
    env_template = """# Transmute Configuration

# Anthropic API Key (required)
# Get your key at: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_api_key_here

# Qdrant Configuration (optional, for RAG)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Model Configuration
CLAUDE_MODEL=claude-sonnet-4-20250514

# Translation Settings
MAX_RETRIES=3
CONFIDENCE_THRESHOLD=0.7
"""
    
    env_file.write_text(env_template)
    
    print_success(f"Created {env_file}")
    print_info("Please edit .env and add your ANTHROPIC_API_KEY")
    console.print()


@config.command('check')
def check_config():
    """
    Check configuration status.
    
    Validates all required settings.
    
    Examples:
    
        transmute config check
    """
    print_header("🔍 Configuration Check")
    
    checks = []
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your_api_key_here":
        checks.append(("ANTHROPIC_API_KEY", True, "Set"))
    else:
        checks.append(("ANTHROPIC_API_KEY", False, "Not set or invalid"))
    
    # Check Qdrant
    try:
        import requests
        response = requests.get("http://localhost:6333/", timeout=2)
        if response.status_code == 200:
            checks.append(("Qdrant", True, "Running"))
        else:
            checks.append(("Qdrant", False, "Not responding"))
    except:
        checks.append(("Qdrant", False, "Not running"))
    
    # Check config files
    config_dir = Path("config/languages")
    if config_dir.exists():
        checks.append(("Language configs", True, f"{len(list(config_dir.glob('*.yaml')))} files"))
    else:
        checks.append(("Language configs", False, "Directory not found"))
    
    # Display results
    for name, status, message in checks:
        if status:
            console.print(f"✓ [green]{name}:[/green] {message}")
        else:
            console.print(f"✗ [red]{name}:[/red] {message}")
    
    console.print()
    
    # Overall status
    all_pass = all(status for _, status, _ in checks)
    if all_pass:
        print_success("All checks passed!")
    else:
        print_error("Some checks failed. Please fix and try again.")


@config.command('show')
def show_config():
    """
    Show current configuration.
    
    Displays all configuration values (masks sensitive data).
    
    Examples:
    
        transmute config show
    """
    print_header("📋 Current Configuration")
    
    settings = {
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', 'Not set'),
        'QDRANT_URL': os.getenv('QDRANT_URL', 'http://localhost:6333'),
        'CLAUDE_MODEL': os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
        'MAX_RETRIES': os.getenv('MAX_RETRIES', '3'),
        'CONFIDENCE_THRESHOLD': os.getenv('CONFIDENCE_THRESHOLD', '0.7')
    }
    
    for key, value in settings.items():
        # Mask API key
        if 'KEY' in key and value != 'Not set':
            display_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
        else:
            display_value = value
        
        console.print(f"[cyan]{key}:[/cyan] {display_value}")
    
    console.print()