# 🔄 Transmute - AI-Powered Code Translation
<!-- Status Badges -->
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-376%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<!-- Technology Stack -->
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.55+-purple.svg)](https://github.com/langchain-ai/langgraph)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.15+-green.svg)](https://github.com/langchain-ai/langchain)
[![Claude AI](https://img.shields.io/badge/Claude-Sonnet%204-orange.svg)](https://www.anthropic.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.12+-red.svg)](https://qdrant.tech/)

<!-- Features -->
[![Languages](https://img.shields.io/badge/languages-6-blue.svg)](README.md#features)
[![Strategies](https://img.shields.io/badge/strategies-4-green.svg)](README.md#translation-strategies)
[![RAG](https://img.shields.io/badge/RAG-enabled-orange.svg)](README.md#features)

<!-- Project Stats -->

> Intelligent code translation between programming languages using Claude AI, RAG, and LangGraph orchestration.

Transmute is a production-ready system that translates code repositories between programming languages while preserving functionality, structure, and idioms. Built with advanced AI techniques including retrieval-augmented generation (RAG), multi-agent orchestration, and intelligent strategy selection.

## ✨ Features

### 🎯 Core Capabilities
- **6 Language Support**: Python, Java, JavaScript, TypeScript, C#, PHP
- **AI-Powered Translation**: Claude Sonnet 4 for intelligent code translation
- **RAG Integration**: Vector search with Qdrant for pattern-based learning
- **Smart Strategies**: Automatic selection of Direct, Pattern, Refactor, or Hybrid approaches
- **Quality Validation**: Automated scoring and confidence metrics
- **Professional CLI**: Beautiful command-line interface with progress tracking

### 🏗️ Architecture Highlights
- **Multi-Agent System**: Specialized agents (Analysis, Planning, Translation, Validation)
- **LangGraph Orchestration**: State-driven workflow with checkpointing
- **Retry Mechanisms**: Exponential backoff with intelligent fallbacks
- **Middleware Pipeline**: Code normalization, comment preservation, quality checks
- **Human-in-the-Loop**: Optional manual review for critical translations

### 🔬 Advanced Features
- **AST Analysis**: Deep code understanding with Tree-sitter
- **Symbol Tables**: Comprehensive scope and type tracking
- **Dependency Graphs**: Relationship mapping and resolution
- **Feature Detection**: Automatic complexity and pattern detection
- **Cross-Language Mapping**: Equivalence matrices for language features

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.12+
python --version

# Docker (for Qdrant vector database)
docker --version

# Anthropic API Key
export ANTHROPIC_API_KEY="your_key_here"
```

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/transmute.git
cd transmute

# Install with Poetry
poetry install

# Start Qdrant (optional, for RAG)
docker-compose up -d
```

### Basic Usage

```bash
# Initialize configuration
transmute config init

# Analyze a repository
transmute analyze https://github.com/user/repo --detailed

# Translate code
transmute translate https://github.com/user/python-app \
    --to java \
    --output ./translated \
    --max-files 10

# List available strategies
transmute strategies list

# Get detailed strategy explanation
transmute strategies explain refactor
```

## 📖 Usage Examples

### 1. Simple Translation (Python → JavaScript)

```bash
transmute translate https://github.com/user/simple-app \
    --to javascript \
    --max-files 5 \
    --strategy direct
```

**Output:**
```
✓ Analysis complete: Python repository (complexity: 0.2)
✓ Created plan: 5 units, strategy=direct
✓ Translation complete: 5/5 files (100% success rate)
✓ Files saved to: output/
```

### 2. Complex Migration (Python → Java)

```bash
transmute translate https://github.com/user/complex-app \
    --to java \
    --strategy refactor \
    --max-files 20
```

**Features:**
- Automatic paradigm shift handling (dynamic → static)
- Type inference and annotation
- Design pattern adaptation
- Framework mapping

### 3. Repository Analysis

```bash
transmute analyze https://github.com/faif/python-patterns --detailed
```

**Output:**
```
Repository Information:
  Language: Python
  Complexity: 0.43 (Medium)
  
Features Used:
  • classes: 45
  • functions: 120
  • decorators: 23
  
Design Patterns: Singleton, Factory, Observer
Framework: pytest
```

### 4. Strategy Comparison

```bash
transmute strategies list
```

**Output:**
```
┌───────────┬──────────────────┬──────────────────────────────┐
│ Strategy  │ Complexity       │ Best For                     │
├───────────┼──────────────────┼──────────────────────────────┤
│ Direct    │ Low (< 0.5)      │ Simple code, similar langs   │
│ Pattern   │ Medium (0.3-0.7) │ Common patterns, RAG ready   │
│ Refactor  │ High (> 0.5)     │ Paradigm shifts, complex     │
│ Hybrid    │ Any              │ Mixed complexity             │
└───────────┴──────────────────┴──────────────────────────────┘
```

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Transmute CLI                         │
└─────────────────────┬───────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │  LangGraph Workflow     │
         │  (State Management)     │
         └────────────┬────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼────┐    ┌──────▼─────┐     ┌─────▼──────┐
│Analysis│───▶│  Planning  │───▶│Translation │
│ Agent  │    │   Agent    │     │   Agent    │
└────────┘    └────────────┘     └─────┬──────┘
                                       │
                                ┌──────▼─────┐
                                │ Validation │
                                │   Agent    │
                                └────────────┘

Supporting Systems:
  • Language Registry (6 plugins)
  • RAG System (Qdrant + Embeddings)
  • Claude API Client
  • Retry Handler + Middleware
```

### System Components

**1. Agents**
- `AnalysisAgent`: Repository analysis and feature detection
- `PlanningAgent`: Strategy selection and execution planning
- `TranslationAgent`: AI-powered code translation
- `ValidationAgent`: Quality scoring and validation

**2. Language System**
- Plugin architecture for language support
- Feature mapping and equivalence matrices
- AST parsing with Tree-sitter
- Symbol table generation

**3. RAG System**
- Vector embeddings with sentence-transformers
- Qdrant vector database
- Pattern retrieval and similarity search
- Context-aware translation

**4. Translation Strategies**
- `DirectStrategy`: 1:1 translation for simple code
- `PatternStrategy`: RAG-based pattern matching
- `RefactorStrategy`: Paradigm shift handling
- `HybridStrategy`: Adaptive multi-strategy approach
- `StrategySelector`: Intelligent strategy recommendation

## 📊 Test Coverage

```bash
# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ --cov=src/transmute --cov-report=html
```

**Test Statistics:**
- Total Tests: 376
- Passing: 376 ✅
- Coverage: ~85%
- Test Categories:
  - Unit Tests: 350+
  - Integration Tests: 20+
  - CLI Tests: 10+

## 🔧 Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_api_key

# Optional
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-20250514
MAX_RETRIES=3
CONFIDENCE_THRESHOLD=0.7
```

### Language Configurations

Each language has a YAML configuration in `config/languages/`:

```yaml
# config/languages/python.yaml
name: Python
version: "3.12"
file_extensions: [".py", ".pyw"]
features:
  - name: classes
    difficulty: easy
  - name: decorators
    difficulty: moderate
```

## 🎯 Translation Strategies

### Strategy Selection Logic

The system automatically selects the best strategy based on:
- **Code Complexity** (0.0-1.0 scale)
- **Feature Mappings** (trivial → impossible)
- **Pattern Availability** (RAG patterns found)
- **Language Compatibility** (paradigm similarity)

### Strategy Comparison

| Strategy | Best For | Complexity | Speed | Quality |
|----------|----------|------------|-------|---------|
| Direct | Simple code, similar languages | < 0.3 | Fast | High |
| Pattern | Common patterns, medium complexity | 0.3-0.7 | Medium | Very High |
| Refactor | Complex code, paradigm shifts | > 0.5 | Slow | High |
| Hybrid | Mixed-complexity codebases | Any | Medium | High |


### Development Setup

```bash
# Install dev dependencies
poetry install --with dev

# Run linters
poetry run black src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/

# Run tests
poetry run pytest tests/ -v
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic Claude**: AI translation engine
- **LangGraph**: Workflow orchestration
- **Qdrant**: Vector database
- **Tree-sitter**: AST parsing

## 📞 Contact

- **Author**: Mohammed Oussiddi
- **Email**: oussiddi.m@gmail.com
- **GitHub**: https://github.com/Oussiddi
