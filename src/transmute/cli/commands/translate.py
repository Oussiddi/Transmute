"""
Translate command - Main translation functionality.
"""

import click
from pathlib import Path
import sys

from transmute.core.state import TransmuteState, RepositoryMetadata, LanguageInfo
from transmute.languages import LanguageRegistry
from transmute.languages.plugins import (
    PythonPlugin, JavaPlugin, JavaScriptPlugin,
    TypeScriptPlugin, CSharpPlugin, PHPPlugin
)
from transmute.rag import RAGSystem
from transmute.llm import ClaudeClient
from transmute.workflows import TransmuteWorkflow
from transmute.cli.ui import (
    print_header, print_success, print_error, print_info,
    print_results_summary, create_progress, console
)
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


@click.command()
@click.argument('repository')
@click.option(
    '--to', '-t',
    'target_language',
    required=True,
    type=click.Choice(['java', 'python', 'javascript', 'typescript', 'csharp', 'php']),
    help='Target language'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='output',
    help='Output directory (default: output)'
)
@click.option(
    '--branch', '-b',
    default='main',
    help='Git branch (default: main)'
)
@click.option(
    '--max-files',
    type=int,
    default=50,
    help='Maximum files to translate (default: 50)'
)
@click.option(
    '--strategy',
    type=click.Choice(['direct', 'pattern', 'refactor', 'hybrid']),
    help='Preferred translation strategy'
)
@click.option(
    '--no-rag',
    is_flag=True,
    help='Disable RAG pattern matching'
)
@click.option(
    '--hitl',
    is_flag=True,
    help='Enable human-in-the-loop review'
)
@click.pass_context
def translate(
    ctx,
    repository,
    target_language,
    output,
    branch,
    max_files,
    strategy,
    no_rag,
    hitl
):
    """
    Translate code repository to another language.
    
    REPOSITORY can be:
    - Git URL: https://github.com/user/repo
    - Local path: /path/to/repo
    
    Examples:
    
        # Translate Python to Java
        transmute translate https://github.com/user/python-app --to java
        
        # With custom output directory
        transmute translate ./my-app --to typescript -o ./translated
        
        # With specific strategy
        transmute translate repo.git --to java --strategy refactor
        
        # Enable human review
        transmute translate repo.git --to java --hitl
    """
    print_header("🚀 Transmute - AI-Powered Code Translation")
    
    try:
        # Check prerequisites
        if not _check_prerequisites(no_rag):
            sys.exit(1)
        
        # Initialize components
        print_info("Initializing components...")
        
        registry = _initialize_registry()
        rag_system = _initialize_rag() if not no_rag else None
        claude_client = ClaudeClient()
        
        # Create workflow
        workflow = TransmuteWorkflow(
            registry=registry,
            rag_system=rag_system,
            claude_client=claude_client,
            use_hitl=hitl
        )
        
        print_success("Components initialized")
        
        # Create initial state
        print_info(f"Repository: {repository}")
        print_info(f"Target: {target_language}")
        print_info(f"Output: {output}")
        
        state = _create_initial_state(
            repository,
            target_language,
            branch,
            output,
            max_files,
            strategy,
            registry
        )
        
        # Run translation
        print_header("📝 Translation Progress")
        
        # Start with initial state
        current_state = state
        
        with create_progress() as progress:
            task = progress.add_task(
                "[cyan]Translating...",
                total=100
            )
            
            # Stream workflow
            for step_output in workflow.stream(state, thread_id="cli"):
                if isinstance(step_output, dict):
                    # Each step_output is {node_name: {updates_dict}}
                    for node_name, updates in step_output.items():
                        # Apply updates to current state
                        if isinstance(updates, dict):
                            for key, value in updates.items():
                                if hasattr(current_state, key):
                                    setattr(current_state, key, value)
                        
                        # Update progress bar
                        if node_name == "translate":
                            if hasattr(current_state, 'migration_plan') and current_state.migration_plan:
                                total = len(current_state.migration_plan.translation_units)
                                completed = sum(
                                    1 for u in current_state.migration_plan.translation_units
                                    if u.status == "completed"
                                )
                                
                                if total > 0:
                                    percent = (completed / total) * 100
                                    progress.update(task, completed=percent)
            
            # Mark as complete
            progress.update(task, completed=100)
        
        # Display results
        print_header("📊 Results")
        
        if current_state.migration_plan:
            plan = current_state.migration_plan
            total = len(plan.translation_units)
            completed = sum(1 for u in plan.translation_units if u.status == "completed")
            failed = sum(1 for u in plan.translation_units if u.status == "failed")
            success_rate = (completed / total * 100) if total > 0 else 0
            
            print_results_summary(total, completed, failed, success_rate)
            
            # Show sample translations
            if completed > 0:
                console.print("\n[bold]Sample Translations:[/bold]")
                for i, unit in enumerate(plan.translation_units):
                    if unit.status == "completed" and i < 5:
                        confidence = unit.confidence_score or 0
                        console.print(f"  • {unit.source_path}: [green]{confidence:.0%}[/green] confidence")
            
            print_success(f"✨ Translations saved to: {output}/")
            
            # Show the actual saved file
            if completed > 0:
                first_completed = next(
                    (u for u in plan.translation_units if u.status == "completed"),
                    None
                )
                if first_completed and first_completed.target_path:
                    console.print(f"\n[bold cyan]View your translation:[/bold cyan]")
                    console.print(f"  {first_completed.target_path}")
        else:
            print_error("No translation plan generated")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print_error("\nTranslation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Translation failed: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print_exception()
        sys.exit(1)


def _check_prerequisites(no_rag: bool) -> bool:
    """Check if prerequisites are met."""
    import os
    
    issues = []
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        issues.append("ANTHROPIC_API_KEY not set")
    
    # Check Qdrant if using RAG
    if not no_rag:
        try:
            import requests
            response = requests.get("http://localhost:6333/", timeout=2)
            if response.status_code != 200:
                issues.append("Qdrant not responding (start with: docker-compose up -d)")
        except:
            issues.append("Qdrant not running (start with: docker-compose up -d)")
    
    if issues:
        print_error("Prerequisites not met:")
        for issue in issues:
            console.print(f"  • {issue}")
        return False
    
    return True


def _initialize_registry() -> LanguageRegistry:
    """Initialize language registry."""
    registry = LanguageRegistry()
    
    # Register all plugins
    registry.register_plugin("python", PythonPlugin)
    registry.register_plugin("java", JavaPlugin)
    registry.register_plugin("javascript", JavaScriptPlugin)
    registry.register_plugin("typescript", TypeScriptPlugin)
    registry.register_plugin("csharp", CSharpPlugin)
    registry.register_plugin("php", PHPPlugin)
    
    return registry


def _initialize_rag() -> RAGSystem:
    """Initialize RAG system."""
    return RAGSystem()


def _create_initial_state(
    repository: str,
    target_language: str,
    branch: str,
    output: str,
    max_files: int,
    strategy: str,
    registry: LanguageRegistry
) -> TransmuteState:
    """Create initial translation state."""
    import uuid
    
    # Create state
    state = TransmuteState(
        session_id=f"cli_{uuid.uuid4().hex[:8]}",
        metadata={
            'output_dir': output,
            'max_files': max_files,  # ← ADD THIS HERE IN CONSTRUCTOR
        }
    )
    
    # Set repository
    state.repository = RepositoryMetadata(
        url=repository,
        platform="github" if "github.com" in repository else "local",
        branch=branch,
        local_path=Path("transmute_work") / f"repo_{state.session_id}"
    )
    
    # Set target language
    if not registry.is_supported(target_language):
        raise ValueError(f"Unsupported target language: {target_language}")
    
    config = registry._configs[target_language]
    state.target_language = LanguageInfo(
        name=config.name,
        version=config.version if hasattr(config, 'version') else None
    )
    
    # Set preferred strategy if specified
    if strategy:
        state.metadata['preferred_strategy'] = strategy
    
    return state