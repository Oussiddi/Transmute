"""
State definitions for Transmute LangGraph workflows.

These Pydantic models define the state that flows through the LangGraph
agents during code migration. Each agent reads and updates this state.
"""

from typing import List, Dict, Any, Optional, Annotated
from pathlib import Path
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RepositoryMetadata(BaseModel):
    """
    Metadata about a cloned repository.
    
    Contains information extracted from the Git repository,
    such as URL, platform, languages, and statistics.
    """
    
    url: str = Field(
        description="Repository URL (e.g., https://github.com/user/repo)"
    )
    
    platform: str = Field(
        description="Git platform (github, gitlab, bitbucket)"
    )
    
    local_path: Optional[Path] = Field(
        default=None,
        description="Local path where repo is cloned"
    )
    
    default_branch: str = Field(
        default="main",
        description="Default branch name"
    )
    
    total_commits: Optional[int] = Field(
        default=None,
        description="Total number of commits"
    )
    
    total_files: int = Field(
        default=0,
        description="Total number of files in repository"
    )
    
    total_lines: int = Field(
        default=0,
        description="Total lines of code"
    )
    
    size_mb: float = Field(
        default=0.0,
        description="Repository size in megabytes"
    )
    
    primary_language: Optional[str] = Field(
        default=None,
        description="Primary programming language detected"
    )
    
    language_distribution: Dict[str, float] = Field(
        default_factory=dict,
        description="Distribution of languages (language: percentage)"
    )
    
    created_at: Optional[datetime] = Field(
        default=None,
        description="Repository creation timestamp"
    )
    
    last_updated: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform is supported."""
        valid_platforms = ['github', 'gitlab', 'bitbucket']
        if v.lower() not in valid_platforms:
            raise ValueError(
                f"Platform must be one of {valid_platforms}, got '{v}'"
            )
        return v.lower()


class LanguageInfo(BaseModel):
    """
    Information about a detected programming language.
    
    Contains details about the source or target language,
    including features, version, and capabilities.
    """
    
    name: str = Field(
        description="Language name (e.g., 'java', 'python')"
    )
    
    version: Optional[str] = Field(
        default=None,
        description="Language version (e.g., '3.11', '17')"
    )
    
    file_count: int = Field(
        default=0,
        description="Number of files in this language"
    )
    
    line_count: int = Field(
        default=0,
        description="Total lines of code in this language"
    )
    
    percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of codebase in this language"
    )
    
    extensions: List[str] = Field(
        default_factory=list,
        description="File extensions for this language"
    )
    
    features_detected: List[str] = Field(
        default_factory=list,
        description="Language features detected in code"
    )


class FeatureType(str, Enum):
    """Types of code features that can be detected."""
    
    CLASSES = "classes"
    INTERFACES = "interfaces"
    INHERITANCE = "inheritance"
    GENERICS = "generics"
    ANNOTATIONS = "annotations"
    ASYNC = "async"
    THREADS = "threads"
    EXCEPTIONS = "exceptions"
    LAMBDAS = "lambdas"
    DECORATORS = "decorators"
    REFLECTION = "reflection"
    METAPROGRAMMING = "metaprogramming"


class FeatureProfile(BaseModel):
    """
    Profile of features detected in source code.
    
    Catalogs what language features are actually used in the code,
    which helps determine the best translation strategy.
    """
    
    language: str = Field(
        description="Source language"
    )
    
    features_used: Dict[str, int] = Field(
        default_factory=dict,
        description="Features used (feature_name: count)"
    )
    
    complexity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall complexity score (0.0 = simple, 1.0 = complex)"
    )
    
    patterns_detected: List[str] = Field(
        default_factory=list,
        description="Design patterns detected (e.g., 'Singleton', 'Factory')"
    )
    
    external_dependencies: List[str] = Field(
        default_factory=list,
        description="External libraries/frameworks used"
    )
    
    framework_detected: Optional[str] = Field(
        default=None,
        description="Main framework detected (e.g., 'Spring Boot', 'Django')"
    )
    
    def has_feature(self, feature: str) -> bool:
        """Check if a feature is used."""
        return feature in self.features_used and self.features_used[feature] > 0
    
    def get_feature_count(self, feature: str) -> int:
        """Get count of how many times a feature is used."""
        return self.features_used.get(feature, 0)
    
    def top_features(self, n: int = 5) -> List[tuple[str, int]]:
        """Get top N most-used features."""
        sorted_features = sorted(
            self.features_used.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_features[:n]


class TranslationStatus(str, Enum):
    """Status of a translation unit."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    TRANSLATED = "translated"
    VALIDATING = "validating"
    VALIDATED = "validated"
    FAILED = "failed"
    COMPLETED = "completed"


class TranslationUnit(BaseModel):
    """
    A single unit of code to be translated.
    
    Represents one file, module, or component that needs translation.
    Tracks its status, dependencies, and translation results.
    """
    
    unit_id: str = Field(
        description="Unique identifier for this unit"
    )
    
    source_path: Path = Field(
        description="Path to source file"
    )
    
    target_path: Optional[Path] = Field(
        default=None,
        description="Path where translated file will be written"
    )
    
    status: TranslationStatus = Field(
        default=TranslationStatus.PENDING,
        description="Current status of translation"
    )
    
    dependencies: List[str] = Field(
        default_factory=list,
        description="IDs of units this depends on"
    )
    
    dependents: List[str] = Field(
        default_factory=list,
        description="IDs of units that depend on this"
    )
    
    priority: int = Field(
        default=0,
        ge=0,
        description="Priority (higher = translate first)"
    )
    
    complexity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Complexity estimate (0.0 = simple, 1.0 = complex)"
    )
    
    source_code: Optional[str] = Field(
        default=None,
        description="Original source code"
    )
    
    translated_code: Optional[str] = Field(
        default=None,
        description="Translated code"
    )
    
    translation_strategy: Optional[str] = Field(
        default=None,
        description="Strategy used for translation"
    )
    
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in translation quality"
    )
    
    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered during translation"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about translation"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    def is_ready_for_translation(self) -> bool:
        """Check if all dependencies are completed."""
        return self.status == TranslationStatus.PENDING
    
    def mark_in_progress(self) -> None:
        """Mark unit as in progress."""
        self.status = TranslationStatus.IN_PROGRESS
    
    def mark_completed(self) -> None:
        """Mark unit as completed."""
        self.status = TranslationStatus.COMPLETED
    
    def mark_failed(self, error: str) -> None:
        """Mark unit as failed."""
        self.status = TranslationStatus.FAILED
        self.errors.append(error)

class StrategyType(str, Enum):
    """Types of translation strategies."""
    
    DIRECT = "direct"  # Simple 1:1 translation
    PATTERN = "pattern"  # Pattern-based with RAG
    REFACTOR = "refactor"  # Requires architectural changes
    HYBRID = "hybrid"  # Combination of strategies


class TranslationStrategy(BaseModel):
    """
    Strategy selected for translating code.
    
    Determines how the translation will be performed based on
    code complexity, features used, and target language capabilities.
    """
    
    strategy_type: StrategyType = Field(
        description="Type of strategy to use"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in strategy selection"
    )
    
    reasoning: str = Field(
        description="Why this strategy was selected"
    )
    
    requires_rag: bool = Field(
        default=False,
        description="Whether RAG lookup is needed"
    )
    
    requires_refactoring: bool = Field(
        default=False,
        description="Whether code refactoring is needed"
    )
    
    estimated_difficulty: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Estimated difficulty (0.0 = easy, 1.0 = hard)"
    )
    
    recommended_patterns: List[str] = Field(
        default_factory=list,
        description="Recommended patterns to use"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional strategy metadata"
    )


class ValidationResult(BaseModel):
    """
    Results from validating translated code.
    
    Contains compilation results, test results, and quality metrics.
    """
    
    is_valid: bool = Field(
        description="Whether validation passed"
    )
    
    compilation_successful: bool = Field(
        default=False,
        description="Whether code compiles"
    )
    
    tests_passed: int = Field(
        default=0,
        ge=0,
        description="Number of tests that passed"
    )
    
    tests_failed: int = Field(
        default=0,
        ge=0,
        description="Number of tests that failed"
    )
    
    compilation_errors: List[str] = Field(
        default_factory=list,
        description="Compilation errors"
    )
    
    runtime_errors: List[str] = Field(
        default_factory=list,
        description="Runtime errors encountered"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Validation warnings"
    )
    
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall quality score"
    )
    
    static_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Static analysis results"
    )
    
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics"
    )
    
    @property
    def test_pass_rate(self) -> float:
        """Calculate test pass rate."""
        total = self.tests_passed + self.tests_failed
        if total == 0:
            return 0.0
        return self.tests_passed / total


class MigrationPlan(BaseModel):
    """
    Complete plan for migrating a repository.
    
    Contains the translation order, dependencies, and overall strategy.
    """
    
    plan_id: str = Field(
        description="Unique identifier for this plan"
    )
    
    source_language: str = Field(
        description="Source language"
    )
    
    target_language: str = Field(
        description="Target language"
    )
    
    total_units: int = Field(
        default=0,
        ge=0,
        description="Total number of translation units"
    )
    
    translation_units: List[TranslationUnit] = Field(
        default_factory=list,
        description="All translation units"
    )
    
    execution_order: List[str] = Field(
        default_factory=list,
        description="Order to execute translations (unit IDs)"
    )
    
    overall_strategy: StrategyType = Field(
        default=StrategyType.HYBRID,
        description="Overall migration strategy"
    )
    
    estimated_duration_minutes: int = Field(
        default=0,
        ge=0,
        description="Estimated time to complete"
    )
    
    estimated_complexity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Overall complexity estimate"
    )
    
    dependencies_resolved: bool = Field(
        default=False,
        description="Whether all dependencies are resolved"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When plan was created"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional plan metadata"
    )
    
    def get_unit(self, unit_id: str) -> Optional[TranslationUnit]:
        """Get a translation unit by ID."""
        for unit in self.translation_units:
            if unit.unit_id == unit_id:
                return unit
        return None
    
    def get_pending_units(self) -> List[TranslationUnit]:
        """Get all pending translation units."""
        return [
            unit for unit in self.translation_units
            if unit.status == TranslationStatus.PENDING
        ]
    
    def get_completed_units(self) -> List[TranslationUnit]:
        """Get all completed translation units."""
        return [
            unit for unit in self.translation_units
            if unit.status == TranslationStatus.COMPLETED
        ]
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_units == 0:
            return 0.0
        completed = len(self.get_completed_units())
        return (completed / self.total_units) * 100.0


class TransmuteState(BaseModel):
    """
    Main state for Transmute LangGraph workflows.
    
    This is the state that flows through all agents in the LangGraph.
    Each agent reads from and writes to this state.
    """
    
    # Session info
    session_id: str = Field(
        description="Unique session identifier"
    )
    
    # Repository info
    repository: Optional[RepositoryMetadata] = Field(
        default=None,
        description="Repository metadata"
    )
    
    # Language info
    source_language: Optional[LanguageInfo] = Field(
        default=None,
        description="Detected source language"
    )
    
    target_language: Optional[LanguageInfo] = Field(
        default=None,
        description="Target language specification"
    )
    
    # Feature analysis
    feature_profile: Optional[FeatureProfile] = Field(
        default=None,
        description="Detected feature profile"
    )
    
    # Migration plan
    migration_plan: Optional[MigrationPlan] = Field(
        default=None,
        description="Complete migration plan"
    )
    
    # Current processing
    current_unit: Optional[TranslationUnit] = Field(
        default=None,
        description="Unit currently being processed"
    )
    
    # Results
    validation_results: List[ValidationResult] = Field(
        default_factory=list,
        description="Validation results for all units"
    )
    
    # Messages (for LangGraph chat history)
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conversation messages"
    )
    
    # Status tracking
    current_step: str = Field(
        default="init",
        description="Current workflow step"
    )
    
    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings generated"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="When workflow started"
    )
    
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When workflow completed"
    )
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_error(self, error: str) -> None:
        """Add an error."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)
    
    def mark_completed(self) -> None:
        """Mark workflow as completed."""
        self.completed_at = datetime.now()
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.completed_at is not None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate workflow duration in seconds."""
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()