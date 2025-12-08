"""
Enhanced Transmute Demo - Showcasing Advanced Features

Demonstrates:
- Agent orchestration
- Retry mechanisms
- Human-in-the-loop (optional)
- Middleware pipelines
- Advanced error handling
"""

import sys
import argparse
import os
import uuid
from pathlib import Path

from transmute.core.state import TransmuteState
from transmute.languages import LanguageRegistry
from transmute.rag import RAGSystem
from transmute.llm import ClaudeClient
from transmute.workflows import TransmuteWorkflow
from transmute.utils.logger import get_logger, setup_logger

# Setup logging
setup_logger(level="INFO")
logger = get_logger(__name__)


# Example repositories
EXAMPLE_REPOS = {
    "python-patterns": {
        "url": "https://github.com/faif/python-patterns",
        "description": "Python design patterns (default)",
        "language": "python"
    },
    "algorithms": {
        "url": "https://github.com/krahets/hello-algo",
        "description": "Algorithm implementations",
        "language": "python"
    },
    "flask-simple": {
        "url": "https://github.com/pallets/flask",
        "description": "Flask web framework",
        "language": "python"
    }
}


def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    issues = []
    
    # Check API key
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        issues.append("❌ ANTHROPIC_API_KEY not set")
    else:
        logger.info("✓ API key found")
    
    # Check Qdrant
    try:
        import requests
        response = requests.get("http://localhost:6333/", timeout=2)
        if response.status_code == 200:
            logger.info("✓ Qdrant running")
        else:
            issues.append("❌ Qdrant not responding")
    except:
        issues.append("❌ Qdrant not running (start with: docker-compose up -d)")
    
    # Check config
    config_path = Path("config/languages")
    if not config_path.exists():
        issues.append("❌ Config directory not found")
    else:
        logger.info("✓ Config directory found")
    
    if issues:
        logger.error("Prerequisites not met:")
        for issue in issues:
            logger.error(f"  {issue}")
        return False
    
    return True


def initialize_rag(registry: LanguageRegistry) -> RAGSystem:
    """Initialize RAG system with example patterns."""
    logger.info("Initializing RAG system...")
    
    rag = RAGSystem()
    
    # Add some example patterns
    example_patterns = [
        {
            "source_language": "python",
            "target_language": "java",
            "feature": "classes",
            "source_code": "class MyClass:\n    def __init__(self):\n        self.value = 0",
            "target_code": "public class MyClass {\n    private int value = 0;\n}",
            "metadata": {
                "complexity": 0.3,
                "confidence": 0.95
            }
        },
        {
            "source_language": "python",
            "target_language": "java",
            "feature": "functions",
            "source_code": "def greet(name):\n    return f'Hello, {name}'",
            "target_code": "public static String greet(String name) {\n    return \"Hello, \" + name;\n}",
            "metadata": {
                "complexity": 0.2,
                "confidence": 0.98
            }
        },
        {
            "source_language": "python",
            "target_language": "java",
            "feature": "list_comprehensions",
            "source_code": "squares = [x**2 for x in range(10)]",
            "target_code": "List<Integer> squares = IntStream.range(0, 10)\n    .map(x -> x * x)\n    .boxed()\n    .collect(Collectors.toList());",
            "metadata": {
                "complexity": 0.6,
                "confidence": 0.85
            }
        },
        {
            "source_language": "python",
            "target_language": "java",
            "feature": "decorators",
            "source_code": "@property\ndef name(self):\n    return self._name",
            "target_code": "public String getName() {\n    return this.name;\n}",
            "metadata": {
                "complexity": 0.5,
                "confidence": 0.80
            }
        },
        {
            "source_language": "python",
            "target_language": "java",
            "feature": "exception_handling",
            "source_code": "try:\n    result = risky_operation()\nexcept ValueError as e:\n    print(e)",
            "target_code": "try {\n    result = riskyOperation();\n} catch (IllegalArgumentException e) {\n    System.out.println(e);\n}",
            "metadata": {
                "complexity": 0.3,
                "confidence": 0.92
            }
        }
    ]
    
    for pattern in example_patterns:
        rag.add_pattern(**pattern)
    
    logger.info(f"Added {len(example_patterns)} example patterns")
    
    return rag

def run_demo(
    repo_url: str,
    target_language: str = "java",
    branch: str = "main",
    use_hitl: bool = False,
    max_files: int = 10
):
    """
    Run the enhanced demo.
    
    Args:
        repo_url: Repository URL
        target_language: Target language
        branch: Git branch
        use_hitl: Enable human-in-the-loop
        max_files: Maximum files to translate
    """
    logger.info("=" * 70)
    logger.info("TRANSMUTE - ENHANCED DEMO")
    logger.info("=" * 70)
    logger.info("")
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Please fix prerequisites and try again")
        sys.exit(1)
    
    logger.info("")
    
    # Initialize components
    logger.info("Initializing Transmute components...")
    
    registry = LanguageRegistry()
    
    # Import and register plugins directly
    from transmute.languages.plugins import (
        PythonPlugin,
        JavaPlugin,
        JavaScriptPlugin,
        TypeScriptPlugin,
        CSharpPlugin,
        PHPPlugin
    )
    
    # Register all plugins (pass CLASSES, not instances)
    registry.register_plugin("python", PythonPlugin)
    registry.register_plugin("java", JavaPlugin)
    registry.register_plugin("javascript", JavaScriptPlugin)
    registry.register_plugin("typescript", TypeScriptPlugin)
    registry.register_plugin("csharp", CSharpPlugin)
    registry.register_plugin("php", PHPPlugin)
    
    logger.info(f"✓ Loaded {len(registry.get_supported_languages())} language plugins")
    
    rag_system = initialize_rag(registry)
    logger.info("✓ RAG system initialized")
    
    claude_client = ClaudeClient()
    logger.info("✓ Claude client initialized")
    
    # Create enhanced workflow with new features
    workflow = TransmuteWorkflow(
        registry=registry,
        rag_system=rag_system,
        claude_client=claude_client,
        use_hitl=use_hitl,
        hitl_confidence_threshold=0.75
    )
    logger.info("✓ Enhanced workflow created")
    
    if use_hitl:
        logger.info("  • Human-in-the-loop: ENABLED")
        logger.info("  • Confidence threshold: 0.75")
    
    logger.info("  • Retry mechanism: ENABLED (max 3 retries)")
    logger.info("  • Middleware pipeline: ENABLED")
    logger.info("    - Code normalization")
    logger.info("    - Comment preservation")
    logger.info("    - Quality checking")
    
    logger.info("")
    
    # Create initial state
    logger.info(f"Repository: {repo_url}")
    logger.info(f"Target Language: {target_language}")
    logger.info(f"Branch: {branch}")
    logger.info("")
    
    # Create initial state
    logger.info(f"Repository: {repo_url}")
    logger.info(f"Target Language: {target_language}")
    logger.info(f"Branch: {branch}")
    logger.info("")
    
    # Check if language is supported
    if not registry.is_supported(target_language):
        logger.error(f"Target language '{target_language}' not found!")
        logger.error(f"Available languages: {', '.join(registry.get_supported_languages())}")
        sys.exit(1)
    
    # Create LanguageInfo from config
    from transmute.core.state import LanguageInfo
    config = registry._configs[target_language]
    target_lang = LanguageInfo(
        name=config.name,
        version=config.version if hasattr(config, 'version') else None
    )
    
    state = TransmuteState(
        session_id=f"demo_{uuid.uuid4().hex[:8]}"
    )
    
    # Create repository metadata object
    from transmute.core.state import RepositoryMetadata
    state.repository = RepositoryMetadata(
        url=repo_url,
        platform="github",  # Could parse from URL
        branch=branch,
        local_path=Path("transmute_work/repo")
    )
    
    # Set target language
    state.target_language = target_lang
    
    # Add to metadata as well
    state.metadata['repository_url'] = repo_url
    state.metadata['target_language_name'] = target_language
    state.metadata['branch'] = branch
    state.metadata['max_files'] = max_files
    
    # Run workflow with streaming
    logger.info("=" * 70)
    logger.info("WORKFLOW EXECUTION")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        file_count = 0
        
        for step_output in workflow.stream(state, thread_id="demo"):
            # Display progress
            if isinstance(step_output, dict):
                for node_name, node_state in step_output.items():
                    if node_name == "translate":
                        # Count files
                        if hasattr(node_state, 'migration_plan') and node_state.migration_plan:
                            completed = sum(
                                1 for unit in node_state.migration_plan.translation_units
                                if unit.status == "completed"
                            )
                            
                            if completed > file_count:
                                file_count = completed
                                logger.info(f"Progress: {file_count} files translated")
                                
                                # Stop after max_files
                                if file_count >= max_files:
                                    logger.info(f"\nReached limit of {max_files} files")
                                    break
        
        final_state = state
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("RESULTS")
        logger.info("=" * 70)
        logger.info("")
        
        # Display results
        if final_state.migration_plan:
            plan = final_state.migration_plan
            
            total_units = len(plan.translation_units)
            completed = sum(1 for u in plan.translation_units if u.status == "completed")
            failed = sum(1 for u in plan.translation_units if u.status == "failed")
            
            logger.info(f"Translation Summary:")
            logger.info(f"  Total files: {total_units}")
            logger.info(f"  Completed: {completed}")
            logger.info(f"  Failed: {failed}")
            logger.info(f"  Success rate: {(completed/total_units*100):.1f}%" if total_units > 0 else "N/A")
            logger.info("")
            
            # Show sample translations
            if completed > 0:
                logger.info("Sample translations:")
                for i, unit in enumerate(plan.translation_units):
                    if unit.status == "completed" and i < 3:
                        confidence = unit.confidence_score or 0
                        logger.info(f"  • {unit.source_path}: {confidence:.0%} confidence")
            
            logger.info("")
            
            # Show output location
            output_dir = Path("demo_output/translations")
            if output_dir.exists():
                file_count = len(list(output_dir.rglob("*.java")))
                logger.info(f"✓ Translations saved to: demo_output/translations/")
                logger.info(f"  {file_count} files created")
        
        # Workflow statistics
        logger.info("")
        logger.info("Workflow Statistics:")
        stats = workflow.get_workflow_statistics()
        
        logger.info(f"  Retry events: {len(stats['retry_history'])}")
        logger.info(f"  Middleware: {', '.join(stats['middleware_enabled'])}")
        
        if 'hitl_statistics' in stats:
            hitl_stats = stats['hitl_statistics']
            logger.info(f"  Reviews performed: {hitl_stats.get('total_reviews', 0)}")
            logger.info(f"  Approval rate: {hitl_stats.get('approval_rate', 0):.0%}")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("DEMO COMPLETE!")
        logger.info("=" * 70)
        
    except KeyboardInterrupt:
        logger.info("\n\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Transmute Enhanced Demo - AI-Powered Code Translation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic demo (default repo)
  python demo.py
  
  # Custom repository
  python demo.py --repo https://github.com/username/repo --target java
  
  # With human-in-the-loop review
  python demo.py --hitl
  
  # Translate more files
  python demo.py --max-files 20
  
  # List example repositories
  python demo.py --list-examples
        """
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        default=EXAMPLE_REPOS['python-patterns']['url'],
        help='Repository URL to translate'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        default='java',
        help='Target language (default: java)'
    )
    
    parser.add_argument(
        '--branch',
        type=str,
        default='main',
        help='Git branch (default: main)'
    )
    
    parser.add_argument(
        '--hitl',
        action='store_true',
        help='Enable human-in-the-loop review'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        default=10,
        help='Maximum files to translate (default: 10)'
    )
    
    parser.add_argument(
        '--list-examples',
        action='store_true',
        help='List example repositories'
    )
    
    args = parser.parse_args()
    
    # List examples
    if args.list_examples:
        print("\nExample Repositories:\n")
        for name, info in EXAMPLE_REPOS.items():
            print(f"  {name}")
            print(f"    URL: {info['url']}")
            print(f"    Description: {info['description']}")
            print()
        sys.exit(0)
    
    # Run demo
    run_demo(
        repo_url=args.repo,
        target_language=args.target,
        branch=args.branch,
        use_hitl=args.hitl,
        max_files=args.max_files
    )


if __name__ == "__main__":
    main()