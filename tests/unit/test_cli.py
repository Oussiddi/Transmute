"""
Tests for CLI commands.
"""

import pytest
from click.testing import CliRunner

from transmute.cli.main import cli


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


class TestCLI:
    """Tests for main CLI."""
    
    def test_cli_help(self, runner):
        """Test CLI help."""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Transmute' in result.output
        assert 'translate' in result.output
        assert 'analyze' in result.output
    
    def test_cli_version(self, runner):
        """Test CLI version."""
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert '0.1.0' in result.output


class TestTranslateCommand:
    """Tests for translate command."""
    
    def test_translate_help(self, runner):
        """Test translate help."""
        result = runner.invoke(cli, ['translate', '--help'])
        
        assert result.exit_code == 0
        assert 'Translate code repository' in result.output
        assert '--to' in result.output
    
    def test_translate_requires_target(self, runner):
        """Test translate requires target language."""
        result = runner.invoke(cli, ['translate', 'repo.git'])
        
        assert result.exit_code != 0
        assert '--to' in result.output or 'required' in result.output.lower()


class TestAnalyzeCommand:
    """Tests for analyze command."""
    
    def test_analyze_help(self, runner):
        """Test analyze help."""
        result = runner.invoke(cli, ['analyze', '--help'])
        
        assert result.exit_code == 0
        assert 'Analyze repository' in result.output


class TestStrategiesCommand:
    """Tests for strategies command."""
    
    def test_strategies_help(self, runner):
        """Test strategies help."""
        result = runner.invoke(cli, ['strategies', '--help'])
        
        assert result.exit_code == 0
    
    def test_strategies_list(self, runner):
        """Test strategies list."""
        result = runner.invoke(cli, ['strategies', 'list'])
        
        assert result.exit_code == 0
        assert 'Direct' in result.output
        assert 'Pattern' in result.output
        assert 'Refactor' in result.output
        assert 'Hybrid' in result.output
    
    def test_strategies_explain(self, runner):
        """Test strategies explain."""
        result = runner.invoke(cli, ['strategies', 'explain', 'pattern'])
        
        assert result.exit_code == 0
        assert 'Pattern' in result.output


class TestConfigCommand:
    """Tests for config command."""
    
    def test_config_help(self, runner):
        """Test config help."""
        result = runner.invoke(cli, ['config', '--help'])
        
        assert result.exit_code == 0
    
    def test_config_check(self, runner):
        """Test config check."""
        result = runner.invoke(cli, ['config', 'check'])
        
        assert result.exit_code == 0
        # Should show some checks
        assert 'API_KEY' in result.output or 'Configuration' in result.output