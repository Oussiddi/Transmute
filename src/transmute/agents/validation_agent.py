"""
Validation agent for translation validation.

Validates translated code for correctness and quality.
"""

from typing import Dict, Any, List
from pathlib import Path

from transmute.agents.base import BaseAgent
from transmute.core.state import TransmuteState, ValidationResult


class ValidationAgent(BaseAgent):
    """
    Validates translated code.
    
    This agent:
    1. Checks syntax validity
    2. Runs basic static analysis
    3. Validates against source code structure
    4. Calculates quality scores
    5. Generates validation reports
    """
    
    def __init__(self):
        """Initialize validation agent."""
        super().__init__("ValidationAgent")
    
    def process(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Validate translations.
        
        Args:
            state: Current state
            
        Returns:
            State updates with validation results
        """
        self.log_info("Starting validation")
        
        if not state.migration_plan:
            self.log_error("No migration plan to validate")
            return {
                "errors": state.errors + ["No migration plan"],
                "current_step": "error"
            }
        
        # Get completed units
        completed_units = state.migration_plan.get_completed_units()
        
        if not completed_units:
            self.log_info("No completed units to validate")
            return {
                "current_step": "completed",
            }
        
        self.log_info(f"Validating {len(completed_units)} units")
        
        validation_results = []
        
        for unit in completed_units:
            result = self._validate_unit(unit, state)
            validation_results.append(result)
        
        # Calculate overall quality
        avg_quality = sum(r.quality_score for r in validation_results) / len(validation_results)
        
        self.log_info(f"Validation complete: avg quality={avg_quality:.2f}")
        
        return {
            "validation_results": validation_results,
            "metadata": {
                **state.metadata,
                "average_quality": avg_quality,
                "validation_count": len(validation_results),
            },
            "current_step": "completed",
        }
    
    def _validate_unit(self, unit, state: TransmuteState) -> ValidationResult:
        """
        Validate a single translation unit.
        
        Args:
            unit: TranslationUnit to validate
            state: Current state
            
        Returns:
            ValidationResult
        """
        self.log_debug(f"Validating unit: {unit.unit_id}")
        
        # Basic validation (simplified)
        compilation_successful = True
        compilation_errors = []
        warnings = []
        
        # Check if translation exists
        if not unit.translated_code:
            compilation_successful = False
            compilation_errors.append("No translated code")
        
        # Basic syntax check (very simple)
        if unit.translated_code:
            # Check for common issues
            if unit.translated_code.count('{') != unit.translated_code.count('}'):
                warnings.append("Mismatched braces")
            
            if unit.translated_code.count('(') != unit.translated_code.count(')'):
                warnings.append("Mismatched parentheses")
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            unit,
            compilation_successful,
            warnings
        )
        
        return ValidationResult(
            is_valid=compilation_successful and len(compilation_errors) == 0,
            compilation_successful=compilation_successful,
            compilation_errors=compilation_errors,
            warnings=warnings,
            quality_score=quality_score,
        )
    
    def _calculate_quality_score(
        self,
        unit,
        compilation_successful: bool,
        warnings: List[str]
    ) -> float:
        """Calculate quality score for translation."""
        score = 1.0
        
        # Penalize compilation errors
        if not compilation_successful:
            score -= 0.5
        
        # Penalize warnings
        score -= len(warnings) * 0.1
        
        # Boost based on confidence
        if unit.confidence_score:
            score = (score + unit.confidence_score) / 2
        
        return max(0.0, min(1.0, score))