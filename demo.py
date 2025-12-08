#!/usr/bin/env python3
"""
Transmute Demo - Real GitHub Repository Translation

Demonstrates complete end-to-end translation of a real GitHub repository!
"""

import os
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from transmute.workflows import TransmuteWorkflow
from transmute.languages.registry import LanguageRegistry
from transmute.languages.plugins import (
    PythonPlugin,
    JavaPlugin,
    JavaScriptPlugin,
    TypeScriptPlugin,
    CSharpPlugin,
    PHPPlugin,
)
from transmute.rag import RAGSystem
from transmute.utils.logger import setup_logger

# Setup logging
setup_logger(level="INFO")


# Small public Python repositories for demo
EXAMPLE_REPOS = {
    "hello-algo": {
        "url": "https://github.com/krahets/hello-algo",
        "description": "Animation-based data structures and algorithms tutorial (has Python code)",
        "target": "java"
    },
    "python-patterns": {
        "url": "https://github.com/faif/python-patterns",
        "description": "Collection of design patterns in Python",
        "target": "java"
    },
    "httpie": {
        "url": "https://github.com/httpie/httpie",
        "description": "Modern HTTP client (might be large, use with caution)",
        "target": "java"
    },
    "rich": {
        "url": "https://github.com/Textualize/rich",
        "description": "Rich text formatting library (might be large)",
        "target": "java"
    },
    "simple": {
        "url": "https://github.com/gto76/python-cheatsheet",
        "description": "Python cheatsheet with code examples",
        "target": "java"
    }
}

# Best for quick demo - very small!
DEFAULT_REPO = "https://github.com/faif/python-patterns"
DEFAULT_TARGET = "java"


def print_banner():
    """Print demo banner."""
    print("=" * 80)
    print("🚀 TRANSMUTE - AI-Powered Code Translation")
    print("   Real GitHub Repository Demo")
    print("=" * 80)
    print()


def print_section(title: str):
    """Print section header."""
    print()
    print("─" * 80)
    print(f"📍 {title}")
    print("─" * 80)


def check_prerequisites():
    """Check if system is ready."""
    print_section("Checking Prerequisites")
    
    all_good = True
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("✅ ANTHROPIC_API_KEY found")
        print("   Will use REAL Claude API for translation!")
    else:
        print("⚠️  ANTHROPIC_API_KEY not set")
        print("   Translation will use placeholder mode")
        print("   Set ANTHROPIC_API_KEY for real translations")
        all_good = False
    
    # Check config directory
    config_dir = Path("config/languages")
    if config_dir.exists():
        print(f"✅ Config directory found: {config_dir}")
    else:
        print(f"❌ Config directory not found: {config_dir}")
        all_good = False
    
    # Check Docker/Qdrant
    try:
        import requests
        response = requests.get("http://localhost:6333/", timeout=2)
        if response.status_code == 200:
            print("✅ Qdrant is running (http://localhost:6333)")
        else:
            print("⚠️  Qdrant responded but might not be ready")
    except:
        print("⚠️  Qdrant not detected (optional)")
        print("   Start with: docker-compose up -d")
        print("   RAG features will be disabled")
    
    print()
    return all_good


def setup_languages():
    """Setup language registry with all plugins."""
    print_section("Setting Up Language Support")
    
    config_dir = Path("config/languages")
    registry = LanguageRegistry(config_dir=config_dir)
    
    # Register all plugins
    plugins = [
        ("python", PythonPlugin),
        ("java", JavaPlugin),
        ("javascript", JavaScriptPlugin),
        ("typescript", TypeScriptPlugin),
        ("csharp", CSharpPlugin),
        ("php", PHPPlugin),
    ]
    
    registered = []
    for name, plugin_class in plugins:
        try:
            registry.register_plugin(name, plugin_class)
            print(f"✅ {name}")
            registered.append(name)
        except Exception as e:
            print(f"⚠️  {name}: {e}")
    
    print(f"\n📊 Total languages: {len(registered)}")
    print(f"   Supported: {', '.join(registered)}")
    
    return registry


def setup_rag():
    """Setup RAG system with example patterns."""
    print_section("Setting Up RAG System")
    
    try:
        rag = RAGSystem(
            qdrant_url="http://localhost:6333",
            collection_name="transmute-demo"
        )
        
        # Add comprehensive example patterns
        example_patterns = [
            # Python to Java - Basic patterns
            {
                "source_code": "for item in items:\n    print(item)",
                "target_code": "for (Item item : items) {\n    System.out.println(item);\n}",
                "source_language": "python",
                "target_language": "java",
                "feature": "for_loop",
                "description": "For loop with print"
            },
            {
                "source_code": "def greet(name):\n    return f'Hello, {name}'",
                "target_code": "public String greet(String name) {\n    return \"Hello, \" + name;\n}",
                "source_language": "python",
                "target_language": "java",
                "feature": "functions",
                "description": "Function with string formatting"
            },
            {
                "source_code": "class Person:\n    def __init__(self, name):\n        self.name = name\n    \n    def greet(self):\n        return f'Hi, {self.name}'",
                "target_code": "public class Person {\n    private String name;\n    \n    public Person(String name) {\n        this.name = name;\n    }\n    \n    public String greet() {\n        return \"Hi, \" + name;\n    }\n}",
                "source_language": "python",
                "target_language": "java",
                "feature": "classes",
                "description": "Class with constructor and method"
            },
            {
                "source_code": "numbers = [1, 2, 3, 4, 5]\nsquares = [x ** 2 for x in numbers]",
                "target_code": "List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);\nList<Integer> squares = numbers.stream()\n    .map(x -> x * x)\n    .collect(Collectors.toList());",
                "source_language": "python",
                "target_language": "java",
                "feature": "comprehensions",
                "description": "List comprehension to stream"
            },
            {
                "source_code": "try:\n    result = risky_operation()\nexcept ValueError as e:\n    print(f'Error: {e}')",
                "target_code": "try {\n    result = riskyOperation();\n} catch (ValueError e) {\n    System.out.println(\"Error: \" + e.getMessage());\n}",
                "source_language": "python",
                "target_language": "java",
                "feature": "exceptions",
                "description": "Exception handling"
            },
        ]
        
        print("📦 Adding example translation patterns...")
        for i, pattern in enumerate(example_patterns, 1):
            rag.add_pattern(**pattern)
            print(f"   {i}. {pattern['feature']}: {pattern['description']}")
        
        stats = rag.get_statistics()
        print(f"\n✅ RAG initialized")
        print(f"   Patterns: {stats['total_patterns']}")
        print(f"   Model: {stats['embedding_model']}")
        print(f"   Dimensions: {stats['embedding_dim']}")
        
        return rag
        
    except Exception as e:
        print(f"⚠️  RAG not available: {e}")
        print("   Continuing without RAG")
        print("   Translations will work but without pattern context")
        return None


def run_demo(repo_url: str, target_language: str, branch: str = None):
    """Run the complete demo."""
    print_banner()
    
    # Show what we're doing
    print(f"📦 Repository: {repo_url}")
    print(f"🎯 Target Language: {target_language}")
    if branch:
        print(f"🌿 Branch: {branch}")
    print()
    
    # Prerequisites
    has_api_key = check_prerequisites()
    
    # Setup
    registry = setup_languages()
    rag_system = setup_rag()
    
    # Create workflow
    print_section("Initializing Transmute Workflow")
    
    workflow = TransmuteWorkflow(
        language_registry=registry,
        work_dir=Path("./transmute_work"),
        use_checkpoints=True
    )
    
    print("✅ Workflow initialized")
    print(f"   • Analysis Agent: Ready")
    print(f"   • Planning Agent: Ready")
    print(f"   • Translation Agent: {'Claude API' if has_api_key else 'Placeholder Mode'}")
    print(f"   • Validation Agent: Ready")
    print(f"   • RAG System: {'Enabled' if rag_system else 'Disabled'}")
    
    # Run translation
    print_section("🚀 Running Complete Translation Pipeline")
    
    print(f"Cloning and analyzing repository...")
    print(f"This may take a minute for larger repos...\n")
    
    try:
        # Stream workflow for real-time updates
        print("📊 Progress:")
        print()
        
        for i, update in enumerate(workflow.stream(
            repository_url=repo_url,
            target_language=target_language,
            branch=branch
        ), 1):
            current_step = update.get('current_step', 'unknown')
            
            if current_step == 'planning':
                print(f"   ✅ Analysis complete")
            elif current_step == 'translation':
                if 'migration_plan' in update:
                    plan = update['migration_plan']
                    completed = len(plan.get_completed_units())
                    total = plan.total_units
                    print(f"   🔄 Translating... {completed}/{total} files")
            elif current_step == 'validation':
                print(f"   ✅ Translation complete")
            elif current_step == 'completed':
                print(f"   ✅ Validation complete")
                break
            elif current_step == 'error':
                print(f"   ❌ Error occurred")
                break
        
        # Get final state
        final_state = workflow.run(repo_url, target_language, branch)
        
        print_section("📊 Translation Results")
        
        # Convert to state object if needed
        from transmute.core.state import TransmuteState
        if isinstance(final_state, dict):
            state_obj = TransmuteState(**final_state)
        else:
            state_obj = final_state
        
        # Display results
        if state_obj.migration_plan:
            plan = state_obj.migration_plan
            
            print(f"\n✨ Translation Complete!")
            print(f"\n📈 Statistics:")
            print(f"   Total Files: {plan.total_units}")
            print(f"   Completed: {len(plan.get_completed_units())}")
            print(f"   Failed: {len([u for u in plan.translation_units if u.status == 'failed'])}")
            print(f"   Strategy: {plan.overall_strategy.value}")
            
            if hasattr(state_obj, 'duration_seconds'):
                print(f"   Duration: {state_obj.duration_seconds:.2f}s")
            
            if state_obj.feature_profile:
                print(f"\n🔍 Code Analysis:")
                print(f"   Complexity: {state_obj.feature_profile.complexity_score:.2f}/1.0")
                print(f"   Features Detected: {len(state_obj.feature_profile.features_used)}")
                
                # Show top features
                top_features = state_obj.feature_profile.top_features(5)
                if top_features:
                    print(f"   Top Features:")
                    for feature, count in top_features:
                        print(f"      • {feature}: {count}")
                
                if state_obj.feature_profile.framework_detected:
                    print(f"   Framework: {state_obj.feature_profile.framework_detected}")
            
            # Show sample translations
            print(f"\n📄 Translated Files:")
            completed_units = plan.get_completed_units()
            
            for i, unit in enumerate(completed_units[:5], 1):  # Show first 5
                print(f"\n   {i}. {unit.source_path}")
                if unit.confidence_score:
                    print(f"      Confidence: {unit.confidence_score:.0%}")
                
                if unit.translated_code:
                    lines = unit.translated_code.split('\n')[:8]
                    print(f"      Translation preview:")
                    for line in lines:
                        print(f"         {line}")
                    if len(unit.translated_code.split('\n')) > 8:
                        total_lines = len(unit.translated_code.split('\n'))
                        print(f"         ... ({total_lines} total lines)")
            
            if len(completed_units) > 5:
                print(f"\n   ... and {len(completed_units) - 5} more files")
        
        else:
            print("\n⚠️  No translations completed")
        
        # Show errors if any
        if hasattr(state_obj, 'errors') and state_obj.errors:
            print(f"\n⚠️  Errors encountered:")
            for error in state_obj.errors[:3]:
                print(f"   • {error}")
            if len(state_obj.errors) > 3:
                print(f"   ... and {len(state_obj.errors) - 3} more")
        
        # Export results
        output_dir = Path("./demo_output")
        print_section("💾 Exporting Results")
        
        result_path = workflow.export_results(state_obj, output_dir)
        
        print(f"✅ Results exported to: {result_path.absolute()}")
        print(f"   • summary.txt - Translation summary")
        
        if (output_dir / "translations").exists():
            translation_count = len(list((output_dir / "translations").glob("*")))
            print(f"   • translations/ - {translation_count} translated files")
        
        print_section("✨ Demo Complete!")
        
        print(f"\n📁 Output directory: {output_dir.absolute()}")
        print(f"🌐 Repository: {repo_url}")
        print(f"🎯 Target: {target_language}")
        
        if not has_api_key:
            print(f"\n💡 Tip: Set ANTHROPIC_API_KEY to see real AI-powered translations!")
        
        # Cleanup
        print_section("🧹 Cleanup")
        try:
            workflow.cleanup(state_obj)
            print("✅ Cleaned up temporary files")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Transmute Demo - Translate real GitHub repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo.py
  python demo.py --repo https://github.com/user/project
  python demo.py --repo https://github.com/user/project --target javascript
  python demo.py --repo https://github.com/user/project --branch develop

Environment Variables:
  ANTHROPIC_API_KEY - Required for real AI translations
  
Example Repos (small Python projects):
  - https://github.com/faif/python-patterns (design patterns)
  - https://github.com/krahets/hello-algo (algorithms tutorial)
"""
    )
    
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repository URL (default: {DEFAULT_REPO})"
    )
    
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        choices=["python", "java", "javascript", "typescript", "csharp", "php"],
        help=f"Target language (default: {DEFAULT_TARGET})"
    )
    
    parser.add_argument(
        "--branch",
        default=None,
        help="Git branch to clone (default: main branch)"
    )
    
    parser.add_argument(
        "--list-examples",
        action="store_true",
        help="List example repositories"
    )
    
    args = parser.parse_args()
    
    if args.list_examples:
        print("📚 Example Repositories:\n")
        for name, info in EXAMPLE_REPOS.items():
            print(f"  {name}:")
            print(f"    URL: {info['url']}")
            print(f"    Description: {info['description']}")
            print(f"    Suggested target: {info['target']}")
            print()
        sys.exit(0)
    
    success = run_demo(args.repo, args.target, args.branch)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()