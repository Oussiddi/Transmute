"""
Configuration management for Transmute.

Handles loading configuration from YAML files, environment variables,
and provides validated configuration objects.
"""

from pathlib import Path
from typing import Any, Dict, Union, Optional
import yaml
import os

from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse YAML file.
    
    Safely loads a YAML file and returns its contents as a dictionary.
    Handles file not found and invalid YAML errors gracefully.
    
    Args:
        file_path: Path to YAML file (string or Path object)
        
    Returns:
        Parsed YAML as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid or cannot be parsed
        
    Example:
        >>> config = load_yaml("config/default.yaml")
        >>> print(config['version'])
        '0.1.0'
        
        >>> config = load_yaml(Path("settings.yml"))
    """
    yaml_path = Path(file_path)
    
    # Check if file exists
    if not yaml_path.exists():
        logger.error(f"YAML file not found: {yaml_path}")
        raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
    
    # Check if it's a file (not a directory)
    if not yaml_path.is_file():
        logger.error(f"Path is not a file: {yaml_path}")
        raise ValueError(f"Path is not a file: {yaml_path}")
    
    # Load and parse YAML
    try:
        logger.debug(f"Loading YAML file: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Handle empty files
        if data is None:
            logger.warning(f"YAML file is empty: {yaml_path}")
            return {}
        
        # Ensure we got a dictionary
        if not isinstance(data, dict):
            logger.error(f"YAML file must contain a dictionary, got {type(data)}")
            raise yaml.YAMLError(
                f"YAML file must contain a dictionary at root level, got {type(data).__name__}"
            )
        
        logger.info(f"Successfully loaded YAML file: {yaml_path}")
        return data
        
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in file {yaml_path}: {e}")
        raise yaml.YAMLError(f"Failed to parse YAML file {yaml_path}: {e}") from e
    
    except Exception as e:
        logger.error(f"Unexpected error loading YAML file {yaml_path}: {e}")
        raise

def merge_configs(
    base: Dict[str, Any],
    override: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deep merge two configuration dictionaries.
    
    Recursively merges the override dictionary into the base dictionary.
    Override values take precedence. Nested dictionaries are merged recursively.
    Lists are replaced (not merged).
    
    Args:
        base: Base configuration dictionary
        override: Override configuration (takes precedence)
        
    Returns:
        Merged configuration dictionary (new dict, doesn't modify inputs)
        
    Example:
        >>> base = {"a": 1, "b": {"x": 10, "y": 20}}
        >>> override = {"b": {"x": 100}, "c": 3}
        >>> result = merge_configs(base, override)
        >>> print(result)
        {'a': 1, 'b': {'x': 100, 'y': 20}, 'c': 3}
        
        >>> base = {"features": ["a", "b"]}
        >>> override = {"features": ["c", "d"]}
        >>> result = merge_configs(base, override)
        >>> print(result)
        {'features': ['c', 'd']}  # Lists are replaced, not merged
    """
    # Create a copy of base to avoid modifying the original
    import copy
    result = copy.deepcopy(base)
    
    # Merge override into result
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Both are dicts - merge recursively
            result[key] = merge_configs(result[key], value)
        else:
            # Override the value (works for all other types including lists)
            result[key] = copy.deepcopy(value)
    
    logger.debug(f"Merged configs: {len(base)} base keys, {len(override)} override keys")
    
    return result

class LLMConfig(BaseModel):
    """
    Configuration for LLM (Large Language Model) settings.
    
    Manages settings for connecting to and using LLMs like Claude, GPT, etc.
    """
    
    provider: str = Field(
        default="anthropic",
        description="LLM provider (anthropic, openai, etc.)"
    )
    
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model identifier"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the LLM provider"
    )
    
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 to 2.0)"
    )
    
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens in response"
    )
    
    timeout: int = Field(
        default=60,
        gt=0,
        description="Request timeout in seconds"
    )
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported."""
        valid_providers = ['anthropic', 'openai', 'azure']
        if v.lower() not in valid_providers:
            raise ValueError(
                f"Provider must be one of {valid_providers}, got '{v}'"
            )
        return v.lower()
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Ensure temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError(
                f"Temperature must be between 0.0 and 2.0, got {v}"
            )
        return v
    
    model_config = ConfigDict(validate_assignment=True)

class RAGConfig(BaseModel):
    """
    Configuration for RAG (Retrieval Augmented Generation) system.
    
    Manages settings for vector store, embeddings, and retrieval.
    Supports multiple vector store backends: Qdrant (default), Chroma, Weaviate, Pinecone.
    """
    
    # Vector Store Settings
    vector_store: str = Field(
        default="qdrant",
        description="Vector store backend (qdrant, chroma, weaviate, pinecone)"
    )
    
    # Qdrant-specific settings
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL"
    )
    
    qdrant_api_key: Optional[str] = Field(
        default=None,
        description="Qdrant API key (for cloud)"
    )
    
    # Chroma-specific settings (fallback option)
    chroma_persist_directory: Optional[str] = Field(
        default=None,
        description="Directory to persist Chroma database"
    )
    
    # Embedding Settings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Model to use for embeddings"
    )
    
    # Collection Settings
    collection_name: str = Field(
        default="transmute-code",
        description="Name of the vector store collection"
    )
    
    # Chunking Settings
    chunk_size: int = Field(
        default=1000,
        gt=0,
        le=8000,
        description="Size of text chunks for embedding"
    )
    
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        description="Overlap between chunks"
    )
    
    # Retrieval Settings
    top_k: int = Field(
        default=5,
        gt=0,
        le=20,
        description="Number of results to retrieve"
    )
    
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for results"
    )
    
    @field_validator('vector_store')
    @classmethod
    def validate_vector_store(cls, v: str) -> str:
        """Validate vector store is supported."""
        valid_stores = ['qdrant', 'chroma', 'weaviate', 'pinecone']
        if v.lower() not in valid_stores:
            raise ValueError(
                f"Vector store must be one of {valid_stores}, got '{v}'"
            )
        return v.lower()
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Ensure chunk overlap is reasonable."""
        if v > 500:  # Sanity check
            raise ValueError(
                f"Chunk overlap seems too large: {v}. Should be < 500."
            )
        return v
    
    @field_validator('qdrant_url')
    @classmethod
    def validate_qdrant_url(cls, v: str) -> str:
        """Ensure Qdrant URL is valid."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError(
                f"Qdrant URL must start with http:// or https://, got '{v}'"
            )
        return v
    
    model_config = ConfigDict(validate_assignment=True)

class TransmuteConfig(BaseSettings):
    """
    Main configuration class for Transmute.
    
    Loads configuration from multiple sources in priority order:
    1. Keyword arguments (highest priority)
    2. Environment variables (prefixed with TRANSMUTE_)
    3. .env file
    4. YAML config file
    5. Defaults (lowest priority)
    
    Example:
        >>> # Load from YAML
        >>> config = TransmuteConfig.from_yaml("config/default.yaml")
        
        >>> # Override with env vars
        >>> os.environ['TRANSMUTE_LLM__MODEL'] = 'gpt-4'
        >>> config = TransmuteConfig()
        
        >>> # Direct initialization
        >>> config = TransmuteConfig(
        ...     llm=LLMConfig(provider="openai"),
        ...     data_dir=Path("/custom/path")
        ... )
    """
    
    model_config = SettingsConfigDict(
        env_prefix="TRANSMUTE_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # Allows TRANSMUTE_LLM__MODEL=value
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields
    )
    
    # Core Settings
    version: str = Field(
        default="0.1.0",
        description="Transmute version"
    )
    
    # LLM Configuration
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM configuration"
    )
    
    # RAG Configuration
    rag: RAGConfig = Field(
        default_factory=RAGConfig,
        description="RAG configuration"
    )
    
    # Path Settings
    data_dir: Path = Field(
        default=Path("/tmp/transmute"),
        description="Base directory for data storage"
    )
    
    # Logging Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    log_file: Optional[str] = Field(
        default=None,
        description="Optional log file path"
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Log level must be one of {valid_levels}, got '{v}'"
            )
        return v.upper()
    
    @field_validator('data_dir')
    @classmethod
    def validate_data_dir(cls, v: Path) -> Path:
        """Convert string to Path if needed."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @classmethod
    def from_yaml(
        cls,
        yaml_path: Union[str, Path] = "config/default.yaml",
        **overrides
    ) -> "TransmuteConfig":
        """
        Create config from YAML file.
        
        Args:
            yaml_path: Path to YAML config file
            **overrides: Additional overrides as keyword arguments
            
        Returns:
            Configured TransmuteConfig instance
            
        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML is invalid
            
        Example:
            >>> config = TransmuteConfig.from_yaml("config/default.yaml")
            >>> config = TransmuteConfig.from_yaml(
            ...     "config/custom.yaml",
            ...     log_level="DEBUG"
            ... )
        """
        logger.info(f"Loading configuration from: {yaml_path}")
        
        # Load YAML file
        yaml_data = load_yaml(yaml_path)
        
        # Handle nested structure (if YAML has 'transmute' key)
        if 'transmute' in yaml_data:
            yaml_data = yaml_data['transmute']
        
        # Merge with overrides
        if overrides:
            yaml_data = merge_configs(yaml_data, overrides)
        
        # Create nested configs if present
        config_data = {}
        
        if 'llm' in yaml_data:
            config_data['llm'] = LLMConfig(**yaml_data['llm'])
        
        if 'rag' in yaml_data:
            config_data['rag'] = RAGConfig(**yaml_data['rag'])
        
        # Copy other top-level keys
        for key, value in yaml_data.items():
            if key not in ['llm', 'rag']:
                config_data[key] = value
        
        return cls(**config_data)
    
    def validate_config(self) -> bool:
        """
        Validate configuration values.
        
        Performs additional validation beyond Pydantic's built-in validation.
        
        Returns:
            True if valid
            
        Raises:
            ValueError: If configuration is invalid
            
        Example:
            >>> config = TransmuteConfig()
            >>> config.validate_config()
            True
        """
        # Validate RAG chunk overlap vs chunk size
        if self.rag.chunk_overlap >= self.rag.chunk_size:
            raise ValueError(
                f"Chunk overlap ({self.rag.chunk_overlap}) must be less than "
                f"chunk size ({self.rag.chunk_size})"
            )
        
        # Validate data directory can be created
        try:
            from transmute.utils.paths import ensure_dir
            ensure_dir(self.data_dir)
        except Exception as e:
            raise ValueError(
                f"Cannot create data directory {self.data_dir}: {e}"
            ) from e
        
        logger.debug("Configuration validation passed")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration as dictionary.
        
        Returns:
            Dictionary representation of configuration
            
        Example:
            >>> config = TransmuteConfig()
            >>> config_dict = config.to_dict()
            >>> print(config_dict['llm']['provider'])
            'anthropic'
        """
        return {
            'version': self.version,
            'llm': self.llm.model_dump(),
            'rag': self.rag.model_dump(),
            'data_dir': str(self.data_dir),
            'log_level': self.log_level,
            'log_file': self.log_file,
        }
    
    def __repr__(self) -> str:
        """String representation of config."""
        return (
            f"TransmuteConfig("
            f"version={self.version}, "
            f"llm={self.llm.provider}/{self.llm.model}, "
            f"rag={self.rag.vector_store}, "
            f"log_level={self.log_level})"
        )