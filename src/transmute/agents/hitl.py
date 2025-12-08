"""
Human-in-the-Loop (HITL) system for manual review and intervention.

Allows humans to review, approve, or correct agent outputs.
"""

from typing import Dict, Any, Optional, Callable
from pathlib import Path
from enum import Enum

from transmute.core.state import TransmuteState, TranslationUnit
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class ReviewDecision(Enum):
    """Human review decisions."""
    APPROVE = "approve"       # Accept as-is
    REJECT = "reject"         # Reject, don't use
    MODIFY = "modify"         # Accept with modifications
    SKIP = "skip"             # Skip for now
    FALLBACK = "fallback"     # Use fallback approach


class HITLSystem:
    """
    Human-in-the-Loop system for manual intervention.
    
    Features:
    - Confidence threshold triggers
    - Manual review interface
    - Correction tracking
    - Quality improvement
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.7,
        review_callback: Optional[Callable] = None
    ):
        """
        Initialize HITL system.
        
        Args:
            confidence_threshold: Minimum confidence to auto-approve
            review_callback: Optional callback for review UI
        """
        self.confidence_threshold = confidence_threshold
        self.review_callback = review_callback
        
        self.review_history: list = []
        self.corrections: list = []
        
        logger.info(
            f"HITLSystem initialized "
            f"(threshold={confidence_threshold})"
        )
    
    def needs_review(
        self,
        unit: TranslationUnit,
        state: TransmuteState
    ) -> bool:
        """
        Determine if translation needs human review.
        
        Args:
            unit: Translation unit
            state: Current state
            
        Returns:
            True if review needed
            
        Example:
            >>> if hitl.needs_review(unit, state):
            ...     decision = hitl.request_review(unit)
        """
        # Check confidence score
        if unit.confidence_score is None:
            return True
        
        if unit.confidence_score < self.confidence_threshold:
            logger.info(
                f"Review needed: {unit.source_path} "
                f"(confidence: {unit.confidence_score:.2f})"
            )
            return True
        
        # Check for errors
        if unit.status == "failed":
            return True
        
        # Check for high complexity
        if hasattr(state, 'feature_profile') and state.feature_profile is not None:
            if state.feature_profile.complexity_score > 0.8:
                logger.info(
                    f"Review needed: {unit.source_path} "
                    f"(high complexity)"
                )
                return True
        
        return False
    
    def request_review(
        self,
        unit: TranslationUnit,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewDecision:
        """
        Request human review of translation.
        
        Args:
            unit: Translation unit to review
            context: Optional context information
            
        Returns:
            Review decision
            
        Example:
            >>> decision = hitl.request_review(unit)
            >>> if decision == ReviewDecision.APPROVE:
            ...     # Accept translation
        """
        logger.info(f"Requesting review for: {unit.source_path}")
        
        review_data = {
            'unit_id': unit.unit_id,
            'source_path': str(unit.source_path),
            'confidence': unit.confidence_score,
            'source_code': unit.source_code[:500] if unit.source_code else None,
            'translated_code': unit.translated_code[:500] if unit.translated_code else None,
            'context': context
        }
        
        # Use callback if provided
        if self.review_callback:
            try:
                decision = self.review_callback(review_data)
                
                if isinstance(decision, str):
                    decision = ReviewDecision(decision)
                
                self._record_review(unit, decision, review_data)
                
                return decision
                
            except Exception as e:
                logger.error(f"Review callback failed: {e}")
        
        # Default: auto-approve if no callback
        logger.warning("No review callback, auto-approving")
        decision = ReviewDecision.APPROVE
        
        self._record_review(unit, decision, review_data)
        
        return decision
    
    def apply_correction(
        self,
        unit: TranslationUnit,
        corrected_code: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Apply human correction to translation.
        
        Args:
            unit: Translation unit
            corrected_code: Corrected code
            notes: Optional correction notes
            
        Example:
            >>> hitl.apply_correction(unit, corrected_java_code, "Fixed syntax")
        """
        logger.info(f"Applying correction to: {unit.source_path}")
        
        # Store original for comparison
        original_code = unit.translated_code
        
        # Apply correction
        unit.translated_code = corrected_code
        unit.confidence_score = 1.0  # Human-corrected = highest confidence
        
        if 'human_reviewed' not in unit.metadata:
            unit.metadata['human_reviewed'] = True
        
        # Record correction
        correction_record = {
            'unit_id': unit.unit_id,
            'source_path': str(unit.source_path),
            'original': original_code,
            'corrected': corrected_code,
            'notes': notes
        }
        
        self.corrections.append(correction_record)
        
        logger.info(f"Correction applied: {unit.source_path}")
    
    def _record_review(
        self,
        unit: TranslationUnit,
        decision: ReviewDecision,
        review_data: Dict[str, Any]
    ) -> None:
        """Record review in history."""
        record = {
            'unit_id': unit.unit_id,
            'source_path': str(unit.source_path),
            'decision': decision.value,
            'confidence': unit.confidence_score,
            **review_data
        }
        
        self.review_history.append(record)
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about reviews.
        
        Returns:
            Statistics dictionary
            
        Example:
            >>> stats = hitl.get_review_statistics()
            >>> print(f"Approval rate: {stats['approval_rate']:.0%}")
        """
        if not self.review_history:
            return {
                'total_reviews': 0,
                'approval_rate': 0.0,
                'correction_rate': 0.0
            }
        
        total = len(self.review_history)
        approved = sum(
            1 for r in self.review_history
            if r['decision'] == ReviewDecision.APPROVE.value
        )
        modified = sum(
            1 for r in self.review_history
            if r['decision'] == ReviewDecision.MODIFY.value
        )
        
        return {
            'total_reviews': total,
            'approval_rate': approved / total,
            'modification_rate': modified / total,
            'correction_count': len(self.corrections)
        }
    
    def export_corrections(self, output_file: Path) -> int:
        """
        Export corrections to file for learning.
        
        Args:
            output_file: Path to output JSON file
            
        Returns:
            Number of corrections exported
            
        Example:
            >>> count = hitl.export_corrections(Path("corrections.json"))
        """
        import json
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.corrections, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(self.corrections)} corrections to {output_file}")
        
        return len(self.corrections)