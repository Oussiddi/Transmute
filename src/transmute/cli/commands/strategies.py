"""
Strategies command - Translation strategy information.
"""

import click

from transmute.strategies import (
    StrategySelector,
    DirectStrategy,
    PatternStrategy,
    RefactorStrategy,
    HybridStrategy
)
from transmute.cli.ui import (
    print_header, create_table, console
)


@click.group()
def strategies():
    """
    Translation strategy information and selection.
    
    Learn about different translation strategies and when to use them.
    """
    pass


@strategies.command('list')
def list_strategies():
    """
    List all available translation strategies.
    
    Examples:
    
        transmute strategies list
    """
    print_header("📋 Translation Strategies")
    
    strategies_info = [
        {
            'name': 'Direct',
            'complexity': 'Low (< 0.5)',
            'best_for': 'Simple code, similar languages',
            'example': 'Python → JavaScript'
        },
        {
            'name': 'Pattern',
            'complexity': 'Medium (0.3-0.7)',
            'best_for': 'Common patterns, moderate complexity',
            'example': 'Python classes → Java classes'
        },
        {
            'name': 'Refactor',
            'complexity': 'High (> 0.5)',
            'best_for': 'Complex code, paradigm shifts',
            'example': 'Python → Java (with types)'
        },
        {
            'name': 'Hybrid',
            'complexity': 'Any',
            'best_for': 'Mixed complexity, adaptive',
            'example': 'Large codebases'
        }
    ]
    
    table = create_table("Available Strategies", ["Strategy", "Complexity", "Best For", "Example"])
    
    for strategy in strategies_info:
        table.add_row(
            strategy['name'],
            strategy['complexity'],
            strategy['best_for'],
            strategy['example']
        )
    
    console.print(table)
    console.print()
    
    console.print("[bold]Usage:[/bold]")
    console.print("  transmute translate repo.git --to java --strategy pattern")
    console.print()


@strategies.command('explain')
@click.argument('strategy_name', type=click.Choice(['direct', 'pattern', 'refactor', 'hybrid']))
def explain_strategy(strategy_name):
    """
    Get detailed explanation of a strategy.
    
    Examples:
    
        transmute strategies explain pattern
        transmute strategies explain refactor
    """
    print_header(f"📖 {strategy_name.capitalize()} Strategy")
    
    explanations = {
        'direct': {
            'description': 'Simple 1:1 translation with minimal changes',
            'when': [
                'Code has low complexity (< 0.5)',
                'Languages have similar paradigms',
                'Features map easily (trivial/easy)',
                'No major restructuring needed'
            ],
            'features': [
                'Minimal context generation',
                'Top 5 feature mappings only',
                'Fast execution',
                'High confidence for simple code'
            ],
            'example': '''
Source (Python):
    def greet(name):
        return f"Hello, {name}"

Target (JavaScript):
    function greet(name) {
        return `Hello, ${name}`;
    }
            '''
        },
        'pattern': {
            'description': 'Uses similar code patterns from RAG database',
            'when': [
                'Medium complexity (0.3-0.7)',
                'Common patterns present',
                'Similar translations exist',
                'Need pattern guidance'
            ],
            'features': [
                'RAG pattern matching',
                'Top 10 feature mappings',
                'Pattern examples included',
                'Moderate context size'
            ],
            'example': '''
Source (Python):
    @property
    def name(self):
        return self._name

Target (Java):
    public String getName() {
        return this.name;
    }
            '''
        },
        'refactor': {
            'description': 'Major restructuring for paradigm shifts',
            'when': [
                'High complexity (> 0.5)',
                'Paradigm differences',
                'Hard feature mappings',
                'Significant changes needed'
            ],
            'features': [
                'Full feature mappings',
                'Alternative approaches',
                'Compatibility warnings',
                'Restructuring guidelines'
            ],
            'example': '''
Source (Python - dynamic):
    data = [x**2 for x in items if x > 0]

Target (Java - static):
    List<Integer> data = items.stream()
        .filter(x -> x > 0)
        .map(x -> x * x)
        .collect(Collectors.toList());
            '''
        },
        'hybrid': {
            'description': 'Combines all strategies adaptively',
            'when': [
                'Mixed complexity codebase',
                'Uncertain complexity',
                'Want best of all approaches',
                'Large projects'
            ],
            'features': [
                'Automatic strategy selection',
                'Per-file adaptation',
                'Combined guidance',
                'Fallback options'
            ],
            'example': '''
Selects strategy based on complexity:
    - Simple functions → Direct
    - Medium classes → Pattern  
    - Complex modules → Refactor
            '''
        }
    }
    
    info = explanations[strategy_name]
    
    console.print(f"[bold]Description:[/bold] {info['description']}")
    console.print()
    
    console.print("[bold]Use When:[/bold]")
    for point in info['when']:
        console.print(f"  • {point}")
    console.print()
    
    console.print("[bold]Features:[/bold]")
    for point in info['features']:
        console.print(f"  • {point}")
    console.print()
    
    console.print("[bold]Example:[/bold]")
    console.print(info['example'])
    console.print()