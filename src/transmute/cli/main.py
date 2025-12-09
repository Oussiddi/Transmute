"""
Transmute CLI - Main entry point.

Professional command-line interface for AI-powered code translation.
"""

import click
from pathlib import Path

from transmute import __version__
from transmute.cli.commands.translate import translate
from transmute.cli.commands.analyze import analyze
from transmute.cli.commands.strategies import strategies
from transmute.cli.commands.config import config
from transmute.utils.logger import setup_logger


@click.group()
@click.version_option(version=__version__, prog_name="transmute")
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress non-error output'
)
@click.pass_context
def cli(ctx, verbose, quiet):
    """
    Transmute - AI-Powered Code Translation
    
    Translate code between programming languages using Claude AI.
    
    Examples:
    
        # Translate a repository
        transmute translate https://github.com/user/repo --to java
        
        # Analyze repository complexity
        transmute analyze https://github.com/user/repo
        
        # List available strategies
        transmute strategies list
        
        # Initialize configuration
        transmute config init
    """
    # Setup logging
    if verbose:
        level = "DEBUG"
    elif quiet:
        level = "ERROR"
    else:
        level = "INFO"
    
    setup_logger(level=level)
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


# Register commands
cli.add_command(translate)
cli.add_command(analyze)
cli.add_command(strategies)
cli.add_command(config)


def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()