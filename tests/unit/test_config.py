"""
Tests for configuration utilities.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from transmute.core.config import (
    load_yaml,
    merge_configs,
    LLMConfig,
    RAGConfig,
    TransmuteConfig,
)


class TestLoadYaml:
    """Tests for load_yaml function."""
    
    def test_load_yaml_valid_file(self):
        """Test loading a valid YAML file."""
        # Use the test config we created
        config_path = Path("config/test_config.yaml")
        
        if not config_path.exists():
            pytest.skip("Test config file not found")
        
        result = load_yaml(config_path)
        
        # Should be a dictionary
        assert isinstance(result, dict)
        
        # Should have expected keys
        assert "version" in result
        assert "app_name" in result
        assert result["app_name"] == "transmute"
    
    def test_load_yaml_with_string_path(self):
        """Test that load_yaml accepts string paths."""
        config_path = "config/test_config.yaml"
        
        if not Path(config_path).exists():
            pytest.skip("Test config file not found")
        
        result = load_yaml(config_path)
        
        assert isinstance(result, dict)
    
    def test_load_yaml_with_path_object(self):
        """Test that load_yaml accepts Path objects."""
        config_path = Path("config/test_config.yaml")
        
        if not config_path.exists():
            pytest.skip("Test config file not found")
        
        result = load_yaml(config_path)
        
        assert isinstance(result, dict)
    
    def test_load_yaml_file_not_found(self):
        """Test that load_yaml raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_yaml("nonexistent_file.yaml")
    
    def test_load_yaml_invalid_yaml(self):
        """Test that load_yaml raises YAMLError for invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Write invalid YAML
            f.write("invalid: yaml: content: [[[")
            temp_path = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                load_yaml(temp_path)
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_load_yaml_empty_file(self):
        """Test that load_yaml handles empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Write nothing
            temp_path = f.name
        
        try:
            result = load_yaml(temp_path)
            # Should return empty dict
            assert result == {}
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_load_yaml_nested_structure(self):
        """Test loading YAML with nested structure."""
        config_path = Path("config/test_config.yaml")
        
        if not config_path.exists():
            pytest.skip("Test config file not found")
        
        result = load_yaml(config_path)
        
        # Should preserve nested structure
        assert "nested" in result
        assert "level1" in result["nested"]
        assert "level2" in result["nested"]["level1"]
        assert result["nested"]["level1"]["level2"]["value"] == "deep"
    
    def test_load_yaml_with_list(self):
        """Test loading YAML containing lists."""
        config_path = Path("config/test_config.yaml")
        
        if not config_path.exists():
            pytest.skip("Test config file not found")
        
        result = load_yaml(config_path)
        
        # Should have list
        assert "features" in result
        assert isinstance(result["features"], list)
        assert "translation" in result["features"]
    
    def test_load_yaml_directory_path(self):
        """Test that load_yaml raises error for directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="not a file"):
                load_yaml(tmpdir)
    
    def test_load_yaml_non_dict_root(self):
        """Test that load_yaml raises error if YAML root is not a dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Write a list at root level
            f.write("- item1\n- item2\n- item3")
            temp_path = f.name
        
        try:
            with pytest.raises(yaml.YAMLError, match="must contain a dictionary"):
                load_yaml(temp_path)
        finally:
            # Clean up
            Path(temp_path).unlink()

class TestMergeConfigs:
    """Tests for merge_configs function."""
    
    def test_merge_configs_simple(self):
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 20, "c": 3}
        
        result = merge_configs(base, override)
        
        # Should have all keys
        assert result == {"a": 1, "b": 20, "c": 3}
    
    def test_merge_configs_nested(self):
        """Test merging nested dictionaries."""
        base = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "mydb"
            }
        }
        override = {
            "database": {
                "host": "remotehost",
                "password": "secret"
            }
        }
        
        result = merge_configs(base, override)
        
        # Should merge nested dicts
        assert result["database"]["host"] == "remotehost"  # Overridden
        assert result["database"]["port"] == 5432  # Preserved from base
        assert result["database"]["name"] == "mydb"  # Preserved from base
        assert result["database"]["password"] == "secret"  # Added from override
    
    def test_merge_configs_deep_nesting(self):
        """Test merging deeply nested structures."""
        base = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "original"
                    }
                }
            }
        }
        override = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "changed"
                    }
                }
            }
        }
        
        result = merge_configs(base, override)
        
        assert result["level1"]["level2"]["level3"]["value"] == "changed"
    
    def test_merge_configs_lists_replaced(self):
        """Test that lists are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        
        result = merge_configs(base, override)
        
        # List should be completely replaced
        assert result["items"] == [4, 5]
    
    def test_merge_configs_empty_override(self):
        """Test merging with empty override."""
        base = {"a": 1, "b": 2}
        override = {}
        
        result = merge_configs(base, override)
        
        # Should be unchanged
        assert result == {"a": 1, "b": 2}
    
    def test_merge_configs_empty_base(self):
        """Test merging with empty base."""
        base = {}
        override = {"a": 1, "b": 2}
        
        result = merge_configs(base, override)
        
        # Should equal override
        assert result == {"a": 1, "b": 2}
    
    def test_merge_configs_doesnt_modify_inputs(self):
        """Test that merge_configs doesn't modify input dictionaries."""
        base = {"a": 1, "b": {"x": 10}}
        override = {"b": {"x": 20}}
        
        # Store original values
        original_base = {"a": 1, "b": {"x": 10}}
        original_override = {"b": {"x": 20}}
        
        result = merge_configs(base, override)
        
        # Inputs should be unchanged
        assert base == original_base
        assert override == original_override
        
        # Result should be different object
        assert result is not base
        assert result is not override
    
    def test_merge_configs_mixed_types(self):
        """Test merging with different value types."""
        base = {
            "string": "hello",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        override = {
            "string": "world",
            "number": 100,
            "boolean": False,
            "new_key": "new_value"
        }
        
        result = merge_configs(base, override)
        
        assert result["string"] == "world"
        assert result["number"] == 100
        assert result["boolean"] is False
        assert result["list"] == [1, 2, 3]  # Preserved
        assert result["dict"] == {"nested": "value"}  # Preserved
        assert result["new_key"] == "new_value"
    
    def test_merge_configs_override_dict_with_value(self):
        """Test overriding a dict with a simple value."""
        base = {"config": {"host": "localhost", "port": 5432}}
        override = {"config": "simple_string"}
        
        result = merge_configs(base, override)
        
        # Dict should be replaced with string
        assert result["config"] == "simple_string"
    
    def test_merge_configs_override_value_with_dict(self):
        """Test overriding a simple value with a dict."""
        base = {"config": "simple_string"}
        override = {"config": {"host": "localhost", "port": 5432}}
        
        result = merge_configs(base, override)
        
        # String should be replaced with dict
        assert result["config"] == {"host": "localhost", "port": 5432}
    
    def test_merge_configs_none_values(self):
        """Test merging with None values."""
        base = {"a": 1, "b": None}
        override = {"b": 2, "c": None}
        
        result = merge_configs(base, override)
        
        assert result == {"a": 1, "b": 2, "c": None}
    
    def test_merge_configs_complex_scenario(self):
        """Test a complex real-world merge scenario."""
        base = {
            "app": {
                "name": "transmute",
                "version": "0.1.0",
                "features": ["basic"]
            },
            "llm": {
                "provider": "anthropic",
                "model": "claude-3",
                "temperature": 0.7
            },
            "logging": {
                "level": "INFO",
                "file": None
            }
        }
        
        override = {
            "app": {
                "features": ["basic", "advanced"]  # Replace list
            },
            "llm": {
                "temperature": 0.1,  # Override value
                "max_tokens": 4000  # Add new key
            },
            "logging": {
                "file": "app.log"  # Override None
            },
            "new_section": {  # Add entire new section
                "enabled": True
            }
        }
        
        result = merge_configs(base, override)
        
        # Check preserved values
        assert result["app"]["name"] == "transmute"
        assert result["app"]["version"] == "0.1.0"
        assert result["llm"]["provider"] == "anthropic"
        assert result["llm"]["model"] == "claude-3"
        assert result["logging"]["level"] == "INFO"
        
        # Check overridden values
        assert result["app"]["features"] == ["basic", "advanced"]
        assert result["llm"]["temperature"] == 0.1
        assert result["logging"]["file"] == "app.log"
        
        # Check new values
        assert result["llm"]["max_tokens"] == 4000
        assert result["new_section"]["enabled"] is True

class TestLLMConfig:
    """Tests for LLMConfig class."""
    
    def test_llm_config_defaults(self):
        """Test LLMConfig with default values."""
        config = LLMConfig()
        
        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-20250514"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096
        assert config.timeout == 60
        assert config.api_key is None
    
    def test_llm_config_custom_values(self):
        """Test LLMConfig with custom values."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
            api_key="test-key"
        )
        
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.api_key == "test-key"
    
    def test_llm_config_invalid_provider(self):
        """Test that invalid provider raises error."""
        with pytest.raises(ValueError, match="Provider must be one of"):
            LLMConfig(provider="invalid_provider")
    
    def test_llm_config_invalid_temperature_high(self):
        """Test that temperature > 2.0 raises error."""
        with pytest.raises(ValueError):
            LLMConfig(temperature=3.0)
    
    def test_llm_config_invalid_temperature_low(self):
        """Test that temperature < 0.0 raises error."""
        with pytest.raises(ValueError):
            LLMConfig(temperature=-0.5)
    
    def test_llm_config_invalid_max_tokens(self):
        """Test that max_tokens <= 0 raises error."""
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=0)
        
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=-100)
    
    def test_llm_config_provider_case_insensitive(self):
        """Test that provider is converted to lowercase."""
        config = LLMConfig(provider="ANTHROPIC")
        assert config.provider == "anthropic"
        
        config = LLMConfig(provider="OpenAI")
        assert config.provider == "openai"
    
    def test_llm_config_from_dict(self):
        """Test creating LLMConfig from dictionary."""
        data = {
            "provider": "anthropic",
            "model": "claude-3",
            "temperature": 0.5
        }
        
        config = LLMConfig(**data)
        
        assert config.provider == "anthropic"
        assert config.model == "claude-3"
        assert config.temperature == 0.5
    
    def test_llm_config_to_dict(self):
        """Test converting LLMConfig to dictionary."""
        config = LLMConfig(provider="openai", temperature=0.8)
        
        data = config.model_dump()
        
        assert isinstance(data, dict)
        assert data["provider"] == "openai"
        assert data["temperature"] == 0.8

class TestRAGConfig:
    """Tests for RAGConfig class."""
    
    def test_rag_config_defaults(self):
        """Test RAGConfig with default values."""
        config = RAGConfig()
        
        assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.vector_store == "qdrant"  # Updated default
        assert config.qdrant_url == "http://localhost:6333"
        assert config.collection_name == "transmute-code"
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.top_k == 5
        assert config.similarity_threshold == 0.7
    
    def test_rag_config_custom_values(self):
        """Test RAGConfig with custom values."""
        config = RAGConfig(
            embedding_model="custom-model",
            vector_store="chroma",
            collection_name="my-collection",
            chunk_size=500,
            chunk_overlap=100,
            top_k=10
        )
        
        assert config.embedding_model == "custom-model"
        assert config.vector_store == "chroma"
        assert config.collection_name == "my-collection"
        assert config.chunk_size == 500
        assert config.chunk_overlap == 100
        assert config.top_k == 10
    
    def test_rag_config_qdrant_settings(self):
        """Test RAGConfig with Qdrant-specific settings."""
        config = RAGConfig(
            vector_store="qdrant",
            qdrant_url="https://my-qdrant-cloud.io",
            qdrant_api_key="test-api-key"
        )
        
        assert config.vector_store == "qdrant"
        assert config.qdrant_url == "https://my-qdrant-cloud.io"
        assert config.qdrant_api_key == "test-api-key"
    
    def test_rag_config_chroma_settings(self):
        """Test RAGConfig with Chroma-specific settings."""
        config = RAGConfig(
            vector_store="chroma",
            chroma_persist_directory="/data/chroma"
        )
        
        assert config.vector_store == "chroma"
        assert config.chroma_persist_directory == "/data/chroma"
    
    def test_rag_config_invalid_vector_store(self):
        """Test that invalid vector store raises error."""
        with pytest.raises(ValueError, match="Vector store must be one of"):
            RAGConfig(vector_store="invalid_store")
    
    def test_rag_config_invalid_chunk_size(self):
        """Test that chunk_size <= 0 raises error."""
        with pytest.raises(ValueError):
            RAGConfig(chunk_size=0)
        
        with pytest.raises(ValueError):
            RAGConfig(chunk_size=-100)
    
    def test_rag_config_chunk_size_too_large(self):
        """Test that chunk_size > 8000 raises error."""
        with pytest.raises(ValueError):
            RAGConfig(chunk_size=10000)
    
    def test_rag_config_invalid_chunk_overlap(self):
        """Test that chunk_overlap < 0 raises error."""
        with pytest.raises(ValueError):
            RAGConfig(chunk_overlap=-10)
    
    def test_rag_config_chunk_overlap_too_large(self):
        """Test that chunk_overlap > 500 raises error."""
        with pytest.raises(ValueError, match="too large"):
            RAGConfig(chunk_overlap=600)
    
    def test_rag_config_invalid_top_k(self):
        """Test that top_k <= 0 raises error."""
        with pytest.raises(ValueError):
            RAGConfig(top_k=0)
    
    def test_rag_config_top_k_too_large(self):
        """Test that top_k > 20 raises error."""
        with pytest.raises(ValueError):
            RAGConfig(top_k=25)
    
    def test_rag_config_invalid_similarity_threshold(self):
        """Test that similarity_threshold out of range raises error."""
        with pytest.raises(ValueError):
            RAGConfig(similarity_threshold=-0.1)
        
        with pytest.raises(ValueError):
            RAGConfig(similarity_threshold=1.5)
    
    def test_rag_config_invalid_qdrant_url(self):
        """Test that invalid Qdrant URL raises error."""
        with pytest.raises(ValueError, match="must start with http"):
            RAGConfig(qdrant_url="invalid-url")
        
        with pytest.raises(ValueError, match="must start with http"):
            RAGConfig(qdrant_url="localhost:6333")
    
    def test_rag_config_vector_store_case_insensitive(self):
        """Test that vector_store is converted to lowercase."""
        config = RAGConfig(vector_store="QDRANT")
        assert config.vector_store == "qdrant"
        
        config = RAGConfig(vector_store="Chroma")
        assert config.vector_store == "chroma"
    
    def test_rag_config_from_dict(self):
        """Test creating RAGConfig from dictionary."""
        data = {
            "vector_store": "weaviate",
            "chunk_size": 800,
            "top_k": 3
        }
        
        config = RAGConfig(**data)
        
        assert config.vector_store == "weaviate"
        assert config.chunk_size == 800
        assert config.top_k == 3
    
    def test_rag_config_to_dict(self):
        """Test converting RAGConfig to dictionary."""
        config = RAGConfig(
            vector_store="qdrant",
            chunk_size=750,
            qdrant_url="http://qdrant:6333"
        )
        
        data = config.model_dump()
        
        assert isinstance(data, dict)
        assert data["vector_store"] == "qdrant"
        assert data["chunk_size"] == 750
        assert data["qdrant_url"] == "http://qdrant:6333"
    
    def test_rag_config_all_vector_stores(self):
        """Test that all supported vector stores work."""
        for store in ['qdrant', 'chroma', 'weaviate', 'pinecone']:
            config = RAGConfig(vector_store=store)
            assert config.vector_store == store


class TestTransmuteConfig:
    """Tests for TransmuteConfig class."""
    
    def test_transmute_config_defaults(self):
        """Test TransmuteConfig with default values."""
        config = TransmuteConfig()
        
        assert config.version == "0.1.0"
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.rag, RAGConfig)
        assert config.log_level == "INFO"
        assert config.log_file is None
        assert isinstance(config.data_dir, Path)
    
    def test_transmute_config_custom_values(self):
        """Test TransmuteConfig with custom values."""
        config = TransmuteConfig(
            version="1.0.0",
            log_level="DEBUG",
            data_dir="/custom/path"
        )
        
        assert config.version == "1.0.0"
        assert config.log_level == "DEBUG"
        assert config.data_dir == Path("/custom/path")
    
    def test_transmute_config_with_nested_configs(self):
        """Test TransmuteConfig with nested LLM and RAG configs."""
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        rag_config = RAGConfig(vector_store="chroma", chunk_size=500)
        
        config = TransmuteConfig(llm=llm_config, rag=rag_config)
        
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4"
        assert config.rag.vector_store == "chroma"
        assert config.rag.chunk_size == 500
    
    def test_transmute_config_from_yaml(self):
        """Test loading TransmuteConfig from YAML file."""
        # Use test_config.yaml or default.yaml
        yaml_path = "config/test_config.yaml"
        if not Path(yaml_path).exists():
            yaml_path = "config/default.yaml"
        
        if not Path(yaml_path).exists():
            pytest.skip("No config file found")
        
        config = TransmuteConfig.from_yaml(yaml_path)
        
        assert isinstance(config, TransmuteConfig)
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.rag, RAGConfig)
    
    def test_transmute_config_from_yaml_with_overrides(self):
        """Test loading from YAML with overrides."""
        yaml_path = "config/test_config.yaml"
        if not Path(yaml_path).exists():
            yaml_path = "config/default.yaml"
        
        if not Path(yaml_path).exists():
            pytest.skip("No config file found")
        
        config = TransmuteConfig.from_yaml(
            yaml_path,
            log_level="DEBUG",
            version="2.0.0"
        )
        
        assert config.log_level == "DEBUG"
        assert config.version == "2.0.0"
    
    def test_transmute_config_invalid_log_level(self):
        """Test that invalid log level raises error."""
        with pytest.raises(ValueError, match="Log level must be one of"):
            TransmuteConfig(log_level="INVALID")
    
    def test_transmute_config_validate_config(self):
        """Test validate_config method."""
        config = TransmuteConfig()
        
        # Should pass validation
        assert config.validate_config() is True
    
    def test_transmute_config_validate_chunk_overlap(self):
        """Test that chunk_overlap >= chunk_size fails validation."""
        rag_config = RAGConfig(chunk_size=100, chunk_overlap=100)
        config = TransmuteConfig(rag=rag_config)
        
        with pytest.raises(ValueError, match="must be less than"):
            config.validate_config()
    
    def test_transmute_config_to_dict(self):
        """Test converting TransmuteConfig to dictionary."""
        config = TransmuteConfig(
            version="1.0.0",
            log_level="DEBUG"
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['version'] == "1.0.0"
        assert config_dict['log_level'] == "DEBUG"
        assert 'llm' in config_dict
        assert 'rag' in config_dict
        assert isinstance(config_dict['llm'], dict)
        assert isinstance(config_dict['rag'], dict)
    
    def test_transmute_config_repr(self):
        """Test string representation of TransmuteConfig."""
        config = TransmuteConfig()
        
        repr_str = repr(config)
        
        assert "TransmuteConfig" in repr_str
        assert "version=" in repr_str
        assert "llm=" in repr_str
    
    def test_transmute_config_data_dir_string_conversion(self):
        """Test that data_dir string is converted to Path."""
        config = TransmuteConfig(data_dir="/tmp/test")
        
        assert isinstance(config.data_dir, Path)
        assert config.data_dir == Path("/tmp/test")
    
    def test_transmute_config_log_level_case_insensitive(self):
        """Test that log_level is converted to uppercase."""
        config = TransmuteConfig(log_level="debug")
        assert config.log_level == "DEBUG"
        
        config = TransmuteConfig(log_level="InFo")
        assert config.log_level == "INFO"