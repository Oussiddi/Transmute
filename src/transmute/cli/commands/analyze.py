"""
Analyze command - Repository analysis.
"""

import click
from pathlib import Path
import sys

from transmute.core.state import TransmuteState, RepositoryMetadata
from transmute.languages import LanguageRegistry
from transmute.languages.plugins import (
    PythonPlugin, JavaPlugin, JavaScriptPlugin,
    TypeScriptPlugin, CSharpPlugin, PHPPlugin
)
from transmute.agents import AnalysisAgent
from transmute.cli.ui import (
    print_header, print_success, print_error, print_info,
    create_table, console
)
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


@click.command()
@click.argument('repository')
@click.option(
    '--branch', '-b',
    default='main',
    help='Git branch (default: main)'
)
@click.option(
    '--detailed',
    is_flag=True,
    help='Show detailed analysis'
)
@click.pass_context
def analyze(ctx, repository, branch, detailed):
    """
    Analyze repository complexity and features.
    
    REPOSITORY can be:
    - Git URL: https://github.com/user/repo
    - Local path: /path/to/repo
    
    Examples:
    
        # Basic analysis
        transmute analyze https://github.com/user/repo
        
        # Detailed analysis
        transmute analyze ./my-app --detailed
        
        # Specific branch
        transmute analyze repo.git --branch develop
    """
    print_header("🔍 Repository Analysis")
    
    try:
        # Initialize components
        print_info("Initializing analysis...")
        
        registry = _initialize_registry()
        analysis_agent = AnalysisAgent(language_registry=registry)
        
        # Create state
        import uuid
        state = TransmuteState(
            session_id=f"analyze_{uuid.uuid4().hex[:8]}"
        )
        
        state.repository = RepositoryMetadata(
            url=repository,
            platform="github" if "github.com" in repository else "local",
            branch=branch,
            local_path=Path("transmute_work") / f"repo_{state.session_id}"
        )
        
        # Run analysis
        print_info(f"Analyzing: {repository}")
        
        result = analysis_agent(state)
        
        # Display results
        print_header("📊 Analysis Results")
        
        if state.source_language:
            console.print(f"[bold]Language:[/bold] {state.source_language.name}")
        
        if state.repository_analysis:
            analysis = state.repository_analysis
            
            # Basic metrics
            table = create_table("Repository Metrics", ["Metric", "Value"])
            table.add_row("Total Files", str(analysis.total_files))
            table.add_row("Code Files", str(analysis.code_files))
            table.add_row("Total Lines", f"{analysis.total_lines:,}")
            table.add_row("Code Lines", f"{analysis.code_lines:,}")
            
            console.print(table)
            console.print()
            
            # Language breakdown
            if analysis.language_breakdown:
                table = create_table("Language Breakdown", ["Language", "Files", "Lines", "Percentage"])
                
                for lang, stats in analysis.language_breakdown.items():
                    table.add_row(
                        lang,
                        str(stats.get('file_count', 0)),
                        f"{stats.get('line_count', 0):,}",
                        f"{stats.get('percentage', 0):.1f}%"
                    )
                
                console.print(table)
                console.print()
        
        if state.feature_profile and detailed:
            profile = state.feature_profile
            
            # Features
            if profile.features_used:
                console.print("[bold]Features Used:[/bold]")
                for feature, count in sorted(
                    profile.features_used.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]:
                    console.print(f"  • {feature}: {count}")
                console.print()
            
            # Complexity
            complexity = profile.complexity_score
            complexity_level = (
                "Low" if complexity < 0.3 else
                "Medium" if complexity < 0.7 else
                "High"
            )
            
            console.print(f"[bold]Complexity:[/bold] {complexity:.2f} ({complexity_level})")
            console.print()
            
            # Patterns
            if profile.patterns_detected:
                console.print("[bold]Design Patterns:[/bold]")
                for pattern in profile.patterns_detected:
                    console.print(f"  • {pattern}")
                console.print()
            
            # Dependencies
            if profile.external_dependencies:
                console.print("[bold]External Dependencies:[/bold]")
                for dep in profile.external_dependencies[:10]:
                    console.print(f"  • {dep}")
                console.print()
        
        print_success("Analysis complete")
        
    except KeyboardInterrupt:
        print_error("\nAnalysis cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Analysis failed: {e}")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


def _initialize_registry() -> LanguageRegistry:
    """Initialize language registry."""
    registry = LanguageRegistry()
    
    registry.register_plugin("python", PythonPlugin)
    registry.register_plugin("java", JavaPlugin)
    registry.register_plugin("javascript", JavaScriptPlugin)
    registry.register_plugin("typescript", TypeScriptPlugin)
    registry.register_plugin("csharp", CSharpPlugin)
    registry.register_plugin("php", PHPPlugin)
    
    return registry