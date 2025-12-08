"""
Symbol table for tracking identifiers and their scopes.

Provides symbol resolution, scope management, and cross-reference tracking.
"""

from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class SymbolKind(Enum):
    """Types of symbols."""
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    PARAMETER = "parameter"
    METHOD = "method"
    PROPERTY = "property"
    MODULE = "module"
    CONSTANT = "constant"


class ScopeType(Enum):
    """Types of scopes."""
    GLOBAL = "global"
    CLASS = "class"
    FUNCTION = "function"
    BLOCK = "block"


@dataclass
class Symbol:
    """
    Represents a symbol (identifier) in code.
    
    Tracks name, type, scope, and references.
    """
    name: str
    kind: SymbolKind
    scope_id: str
    line: int
    column: int = 0
    
    # Type information
    type_annotation: Optional[str] = None
    inferred_type: Optional[str] = None
    
    # References
    definitions: List[tuple] = field(default_factory=list)  # [(line, col)]
    references: List[tuple] = field(default_factory=list)   # [(line, col)]
    
    # Additional metadata
    is_exported: bool = False
    is_imported: bool = False
    visibility: str = "public"  # public, private, protected
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_reference(self, line: int, column: int) -> None:
        """Add a reference to this symbol."""
        self.references.append((line, column))
    
    def add_definition(self, line: int, column: int) -> None:
        """Add a definition of this symbol."""
        self.definitions.append((line, column))
    
    def get_reference_count(self) -> int:
        """Get number of references."""
        return len(self.references)
    
    def is_unused(self) -> bool:
        """Check if symbol is unused."""
        return len(self.references) == 0


@dataclass
class Scope:
    """
    Represents a scope in code.
    
    Manages symbols within a specific scope level.
    """
    scope_id: str
    scope_type: ScopeType
    parent_id: Optional[str] = None
    
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    
    # Scope metadata
    name: Optional[str] = None  # Function/class name
    line_start: int = 0
    line_end: int = 0
    
    def add_symbol(self, symbol: Symbol) -> None:
        """Add symbol to scope."""
        self.symbols[symbol.name] = symbol
    
    def get_symbol(self, name: str) -> Optional[Symbol]:
        """Get symbol by name."""
        return self.symbols.get(name)
    
    def has_symbol(self, name: str) -> bool:
        """Check if symbol exists in scope."""
        return name in self.symbols
    
    def get_all_symbols(self) -> List[Symbol]:
        """Get all symbols in scope."""
        return list(self.symbols.values())


class SymbolTable:
    """
    Symbol table for tracking all identifiers in code.
    
    Features:
    - Multi-level scoping
    - Symbol resolution
    - Cross-reference tracking
    - Unused symbol detection
    """
    
    def __init__(self):
        """Initialize symbol table."""
        self.scopes: Dict[str, Scope] = {}
        self.current_scope_id: str = "global"
        self.scope_counter: int = 0
        
        # Create global scope
        self._create_scope("global", ScopeType.GLOBAL)
        
        logger.debug("SymbolTable initialized")
    
    def _create_scope(
        self,
        scope_id: str,
        scope_type: ScopeType,
        parent_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> Scope:
        """Create a new scope."""
        scope = Scope(
            scope_id=scope_id,
            scope_type=scope_type,
            parent_id=parent_id,
            name=name
        )
        
        self.scopes[scope_id] = scope
        
        # Add to parent's children
        if parent_id and parent_id in self.scopes:
            self.scopes[parent_id].children.append(scope_id)
        
        return scope
    
    def enter_scope(
        self,
        scope_type: ScopeType,
        name: Optional[str] = None
    ) -> str:
        """
        Enter a new scope.
        
        Args:
            scope_type: Type of scope
            name: Optional scope name
            
        Returns:
            New scope ID
            
        Example:
            >>> scope_id = table.enter_scope(ScopeType.FUNCTION, "my_function")
        """
        self.scope_counter += 1
        scope_id = f"{scope_type.value}_{self.scope_counter}"
        
        self._create_scope(
            scope_id=scope_id,
            scope_type=scope_type,
            parent_id=self.current_scope_id,
            name=name
        )
        
        self.current_scope_id = scope_id
        
        logger.debug(f"Entered scope: {scope_id}")
        
        return scope_id
    
    def exit_scope(self) -> Optional[str]:
        """
        Exit current scope and return to parent.
        
        Returns:
            Parent scope ID, or None if at global scope
            
        Example:
            >>> table.exit_scope()
        """
        current = self.scopes.get(self.current_scope_id)
        
        if current and current.parent_id:
            self.current_scope_id = current.parent_id
            logger.debug(f"Exited to scope: {self.current_scope_id}")
            return self.current_scope_id
        
        return None
    
    def add_symbol(
        self,
        name: str,
        kind: SymbolKind,
        line: int,
        column: int = 0,
        **kwargs
    ) -> Symbol:
        """
        Add a symbol to current scope.
        
        Args:
            name: Symbol name
            kind: Symbol kind
            line: Line number
            column: Column number
            **kwargs: Additional symbol attributes
            
        Returns:
            Created symbol
            
        Example:
            >>> symbol = table.add_symbol("count", SymbolKind.VARIABLE, 10)
        """
        symbol = Symbol(
            name=name,
            kind=kind,
            scope_id=self.current_scope_id,
            line=line,
            column=column,
            **kwargs
        )
        
        # Add definition
        symbol.add_definition(line, column)
        
        # Add to current scope
        current_scope = self.scopes[self.current_scope_id]
        current_scope.add_symbol(symbol)
        
        logger.debug(f"Added symbol: {name} ({kind.value}) at {line}:{column}")
        
        return symbol
    
    def lookup_symbol(
        self,
        name: str,
        scope_id: Optional[str] = None
    ) -> Optional[Symbol]:
        """
        Look up symbol by name, searching parent scopes if needed.
        
        Args:
            name: Symbol name
            scope_id: Optional specific scope to search from
            
        Returns:
            Symbol if found, None otherwise
            
        Example:
            >>> symbol = table.lookup_symbol("my_var")
            >>> if symbol:
            ...     print(f"Found at line {symbol.line}")
        """
        search_scope_id = scope_id or self.current_scope_id
        
        # Search current scope and parents
        while search_scope_id:
            scope = self.scopes.get(search_scope_id)
            
            if scope and scope.has_symbol(name):
                return scope.get_symbol(name)
            
            # Move to parent scope
            search_scope_id = scope.parent_id if scope else None
        
        return None
    
    def add_reference(
        self,
        name: str,
        line: int,
        column: int = 0
    ) -> bool:
        """
        Add a reference to a symbol.
        
        Args:
            name: Symbol name
            line: Line number
            column: Column number
            
        Returns:
            True if symbol found and reference added
            
        Example:
            >>> table.add_reference("my_var", 15)
        """
        symbol = self.lookup_symbol(name)
        
        if symbol:
            symbol.add_reference(line, column)
            logger.debug(f"Added reference to {name} at {line}:{column}")
            return True
        else:
            logger.warning(f"Symbol not found for reference: {name} at {line}:{column}")
            return False
    
    def get_all_symbols(self) -> List[Symbol]:
        """
        Get all symbols from all scopes.
        
        Returns:
            List of all symbols
            
        Example:
            >>> all_symbols = table.get_all_symbols()
            >>> print(f"Total symbols: {len(all_symbols)}")
        """
        symbols = []
        
        for scope in self.scopes.values():
            symbols.extend(scope.get_all_symbols())
        
        return symbols
    
    def get_symbols_by_kind(self, kind: SymbolKind) -> List[Symbol]:
        """
        Get all symbols of specific kind.
        
        Args:
            kind: Symbol kind to filter by
            
        Returns:
            List of matching symbols
            
        Example:
            >>> functions = table.get_symbols_by_kind(SymbolKind.FUNCTION)
        """
        return [
            symbol for symbol in self.get_all_symbols()
            if symbol.kind == kind
        ]
    
    def get_unused_symbols(self) -> List[Symbol]:
        """
        Get all unused symbols (defined but never referenced).
        
        Returns:
            List of unused symbols
            
        Example:
            >>> unused = table.get_unused_symbols()
            >>> for symbol in unused:
            ...     print(f"Unused: {symbol.name} at line {symbol.line}")
        """
        return [
            symbol for symbol in self.get_all_symbols()
            if symbol.is_unused() and symbol.kind != SymbolKind.FUNCTION
        ]
    
    def get_scope_hierarchy(self) -> Dict[str, Any]:
        """
        Get scope hierarchy as nested dictionary.
        
        Returns:
            Nested scope structure
            
        Example:
            >>> hierarchy = table.get_scope_hierarchy()
        """
        def build_tree(scope_id: str) -> Dict[str, Any]:
            scope = self.scopes[scope_id]
            
            return {
                'id': scope_id,
                'type': scope.scope_type.value,
                'name': scope.name,
                'symbols': len(scope.symbols),
                'children': [build_tree(child_id) for child_id in scope.children]
            }
        
        return build_tree("global")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get symbol table statistics.
        
        Returns:
            Statistics dictionary
            
        Example:
            >>> stats = table.get_statistics()
            >>> print(f"Total symbols: {stats['total_symbols']}")
        """
        all_symbols = self.get_all_symbols()
        
        return {
            'total_symbols': len(all_symbols),
            'total_scopes': len(self.scopes),
            'functions': len(self.get_symbols_by_kind(SymbolKind.FUNCTION)),
            'classes': len(self.get_symbols_by_kind(SymbolKind.CLASS)),
            'variables': len(self.get_symbols_by_kind(SymbolKind.VARIABLE)),
            'unused_symbols': len(self.get_unused_symbols()),
            'max_scope_depth': self._calculate_max_depth()
        }
    
    def _calculate_max_depth(self) -> int:
        """Calculate maximum scope nesting depth."""
        def get_depth(scope_id: str) -> int:
            scope = self.scopes[scope_id]
            
            if not scope.children:
                return 1
            
            return 1 + max(get_depth(child_id) for child_id in scope.children)
        
        return get_depth("global")
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export symbol table to dictionary.
        
        Returns:
            Dictionary representation
            
        Example:
            >>> data = table.export_to_dict()
        """
        return {
            'scopes': {
                scope_id: {
                    'type': scope.scope_type.value,
                    'name': scope.name,
                    'parent': scope.parent_id,
                    'symbols': [
                        {
                            'name': sym.name,
                            'kind': sym.kind.value,
                            'line': sym.line,
                            'references': len(sym.references)
                        }
                        for sym in scope.get_all_symbols()
                    ]
                }
                for scope_id, scope in self.scopes.items()
            },
            'statistics': self.get_statistics()
        }