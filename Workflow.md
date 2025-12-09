# 🔄 Transmute Workflow Guide

Complete guide to how Transmute's workflow executes, how agents communicate, and where streaming is used.

## Table of Contents

- [Overview](#overview)
- [Workflow Execution Flow](#workflow-execution-flow)
- [Agent Communication](#agent-communication)
- [State Management](#state-management)
- [Streaming vs Invoke](#streaming-vs-invoke)
- [Complete Example](#complete-example)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)

## Overview

Transmute uses **LangGraph** for workflow orchestration. The workflow is a directed graph where:
- **Nodes** = Agents (Analysis, Planning, Translation, Validation)
- **Edges** = Data flow between agents
- **State** = Shared context (TransmuteState) that flows through the graph

```
Entry Point
    ↓
[Analysis Node]
    ↓ (state updates)
[Planning Node]
    ↓ (state updates)
[Translation Node]
    ↓ (state updates)
[Validation Node]
    ↓
END
```

## Workflow Execution Flow

### 1. Initialization

**Location**: `src/transmute/workflows/transmute_workflow.py`

```python
class TransmuteWorkflow:
    def __init__(
        self,
        registry: LanguageRegistry,
        rag_system: Optional[RAGSystem] = None,
        claude_client: Optional[ClaudeClient] = None,
        use_hitl: bool = False
    ):
        # Initialize all agents
        self.analysis_agent = AnalysisAgent(language_registry=registry)
        self.planning_agent = PlanningAgent(language_registry=registry)
        self.translation_agent = TranslationAgent(
            rag_system=rag_system,
            claude_client=claude_client
        )
        self.validation_agent = ValidationAgent()
        
        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator()
        self.orchestrator.register_agent("analysis", self.analysis_agent)
        self.orchestrator.register_agent("planning", self.planning_agent)
        self.orchestrator.register_agent("translation", self.translation_agent)
        self.orchestrator.register_agent("validation", self.validation_agent)
        self.orchestrator.set_execution_order([
            "analysis", "planning", "translation", "validation"
        ])
        
        # Build LangGraph
        self.graph = self._build_graph()
```

### 2. Graph Construction

**What it does**: Defines the workflow structure

```python
def _build_graph(self) -> CompiledGraph:
    """Build LangGraph workflow."""
    
    # Create state graph
    graph = StateGraph(TransmuteState)
    
    # Add nodes (wrap agents in node methods)
    graph.add_node("analyze", self._analyze_node)
    graph.add_node("plan", self._plan_node)
    graph.add_node("translate", self._translate_node)
    graph.add_node("validate", self._validate_node)
    
    # Define edges (execution flow)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "plan")
    graph.add_edge("plan", "translate")
    graph.add_edge("translate", "validate")
    graph.add_edge("validate", END)
    
    # Add checkpointer for state persistence
    memory = MemorySaver()
    
    # Compile graph
    return graph.compile(checkpointer=memory)
```

**Key Concepts**:
- `StateGraph(TransmuteState)` - Creates graph with typed state
- `add_node(name, function)` - Adds agent wrapper function
- `add_edge(from, to)` - Connects nodes
- `compile(checkpointer)` - Builds executable graph

### 3. Node Methods (Agent Wrappers)

Each node wraps an agent and handles:
- Retry logic
- Middleware application
- Logging
- State updates

#### Example: Analysis Node

```python
def _analyze_node(self, state: TransmuteState) -> Dict[str, Any]:
    """
    Analysis node - wraps AnalysisAgent.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dictionary of state updates
    """
    logger.info("📊 Running analysis...")
    
    # Wrap agent call in retry handler
    updates = self.retry_handler.execute_with_retry(
        func=lambda: self.analysis_agent(state),
        operation_name="analysis"
    )
    
    return updates
```

#### Example: Translation Node (with Middleware)

```python
def _translate_node(self, state: TransmuteState) -> Dict[str, Any]:
    """
    Translation node - wraps TranslationAgent with middleware.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dictionary of state updates
    """
    logger.info("🔄 Translating code...")
    
    # Apply middleware BEFORE translation
    processed_state = self.middleware.pre_process(state)
    
    # Execute translation with retry + fallback
    try:
        updates = self.retry_handler.execute_with_retry(
            func=lambda: self.translation_agent(processed_state),
            operation_name="translation",
            fallback=lambda: self._fallback_translation(processed_state)
        )
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        updates = self._fallback_translation(processed_state)
    
    # Apply middleware AFTER translation
    final_updates = self.middleware.post_process(updates)
    
    return final_updates
```

**What happens here**:
1. Middleware pre-processes state (normalize code, extract comments)
2. Agent executes with retry logic
3. If all retries fail → fallback translation
4. Middleware post-processes result (restore comments, quality check)
5. Return state updates

## Agent Communication

### How Agents Talk to Each Other

**Agents DON'T directly communicate!** Instead, they:
1. Read from shared state
2. Execute their logic
3. Return state updates
4. LangGraph merges updates into state

### State Update Pattern

**Every agent returns a dict of updates:**

```python
class AnalysisAgent(BaseAgent):
    def process(self, state: TransmuteState) -> Dict[str, Any]:
        # Read from state
        repo_url = state.repository.url
        
        # Do work
        analysis_results = self._analyze(repo_url)
        
        # Return updates
        return {
            "source_language": detected_language,
            "feature_profile": feature_profile,
            "metadata": {
                **state.metadata,
                "analysis_time": time_taken
            },
            "current_step": "planning"
        }
```

**LangGraph automatically merges these updates into state:**

```python
# Before agent call
state.source_language = None
state.feature_profile = None

# Agent returns updates
updates = agent(state)

# After LangGraph merge
state.source_language = "python"  # ✅ Updated
state.feature_profile = FeatureProfile(...)  # ✅ Updated
```

### Agent Responsibilities

#### 1. AnalysisAgent

**Input**: Repository URL from state
**Output**: Language info, feature profile, file mappings

```python
def process(self, state: TransmuteState) -> Dict[str, Any]:
    """
    Analyzes repository to understand codebase.
    
    Reads from state:
    - state.repository.url
    - state.repository.branch
    
    Updates state with:
    - source_language
    - feature_profile
    - metadata['file_map']
    - current_step = "planning"
    """
    # Clone repo
    repo = GitRepository(state.repository.url)
    repo.clone()
    
    # Detect languages
    languages = self.repository_analyzer.detect_languages(repo)
    
    # Build feature profile
    features = self.feature_detector.build_feature_profile(
        git_repo=repo,
        file_map=file_map,
        primary_language=languages[0]
    )
    
    return {
        "source_language": languages[0],
        "feature_profile": features,
        "metadata": {
            **state.metadata,
            "file_map": file_map,
            "clone_path": str(repo.local_path)
        },
        "current_step": "planning"
    }
```

#### 2. PlanningAgent

**Input**: Analysis results from state
**Output**: Migration plan with translation units

```python
def process(self, state: TransmuteState) -> Dict[str, Any]:
    """
    Creates translation strategy and execution plan.
    
    Reads from state:
    - state.source_language
    - state.target_language
    - state.feature_profile
    - state.metadata['file_map']
    - state.metadata['max_files']
    
    Updates state with:
    - migration_plan
    - current_step = "translation"
    """
    # Get files to translate
    file_map = state.metadata.get('file_map', {})
    source_lang = state.source_language.name
    files = file_map[source_lang]
    
    # Respect max_files limit
    max_files = state.metadata.get('max_files')
    if max_files and max_files > 0:
        files = files[:max_files]
    
    # Create translation units
    translation_units = []
    for file_path in files:
        unit = TranslationUnit(
            unit_id=str(uuid.uuid4()),
            source_path=Path(file_path),
            status=TranslationStatus.PENDING
        )
        translation_units.append(unit)
    
    # Select strategy
    complexity = state.feature_profile.complexity_score
    if complexity < 0.3:
        strategy = StrategyType.DIRECT
    elif complexity < 0.7:
        strategy = StrategyType.PATTERN
    else:
        strategy = StrategyType.REFACTOR
    
    # Create plan
    plan = MigrationPlan(
        plan_id=str(uuid.uuid4()),
        source_language=source_lang,
        target_language=state.target_language.name,
        total_units=len(translation_units),
        translation_units=translation_units,
        overall_strategy=strategy
    )
    
    return {
        "migration_plan": plan,
        "current_step": "translation"
    }
```

#### 3. TranslationAgent

**Input**: Migration plan from state
**Output**: Translated code for all pending units

```python
def process(self, state: TransmuteState) -> Dict[str, Any]:
    """
    Translates code using LLM and RAG.
    
    Reads from state:
    - state.migration_plan (translation units)
    - state.source_language
    - state.target_language
    - state.feature_profile
    - state.metadata['clone_path']
    
    Updates state with:
    - migration_plan (updated with translations)
    - current_step = "validation"
    """
    plan = state.migration_plan
    pending = plan.get_pending_units()
    
    # Translate ALL pending units
    for unit in pending:
        # Load source code
        clone_path = state.metadata.get('clone_path')
        file_path = Path(clone_path) / unit.source_path
        unit.source_code = file_path.read_text()
        
        # Get RAG patterns (if available)
        context_patterns = None
        if self.rag_system:
            context_patterns = self.rag_system.retrieve_context(
                query_code=unit.source_code[:500],
                source_language=state.source_language.name,
                target_language=state.target_language.name
            )
        
        # Translate with Claude
        result = self.claude_client.translate_code(
            source_code=unit.source_code,
            source_language=state.source_language.name,
            target_language=state.target_language.name,
            feature_profile=state.feature_profile,
            context_patterns=context_patterns
        )
        
        # Update unit
        unit.translated_code = result['translated_code']
        unit.confidence_score = result.get('confidence', 0.8)
        unit.mark_completed()
        
        # Save to disk
        output_file = self._get_output_path(unit, state)
        output_file.write_text(unit.translated_code)
    
    return {
        "migration_plan": plan,
        "current_step": "validation"
    }
```

#### 4. ValidationAgent

**Input**: Completed translations from state
**Output**: Quality scores and validation results

```python
def process(self, state: TransmuteState) -> Dict[str, Any]:
    """
    Validates translation quality.
    
    Reads from state:
    - state.migration_plan (translated units)
    
    Updates state with:
    - validation_results
    - current_step = "complete"
    """
    plan = state.migration_plan
    completed = plan.get_completed_units()
    
    validation_results = []
    
    for unit in completed:
        # Validate syntax, structure, completeness
        result = ValidationResult(
            unit_id=unit.unit_id,
            is_valid=self._validate_syntax(unit.translated_code),
            quality_score=self._calculate_quality(unit),
            issues_found=[],
            suggestions=[]
        )
        
        validation_results.append(result)
    
    return {
        "validation_results": validation_results,
        "current_step": "complete"
    }
```

## Streaming vs Invoke

### When to Use Each

| Method | Use Case | Returns | Example |
|--------|----------|---------|---------|
| `invoke()` | Single execution, get final state | Complete state | Unit tests |
| `stream()` | Monitor progress, live updates | Generator of updates | CLI, UI |

### Using `invoke()` - Synchronous Execution

**Location**: Direct execution, unit tests

```python
def run(
    self,
    initial_state: TransmuteState,
    thread_id: str = "default"
) -> TransmuteState:
    """
    Run workflow synchronously.
    
    Use when:
    - You want the final result only
    - No need for progress updates
    - Simple scripts or tests
    
    Returns:
        Final state after all agents complete
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Invoke returns final state
    final_state = self.graph.invoke(initial_state, config)
    
    return final_state


# Example usage
workflow = TransmuteWorkflow(...)
state = TransmuteState(session_id="test-001", ...)

# Execute and get final result
final_state = workflow.run(state)

# Access results
print(f"Translated {len(final_state.migration_plan.translation_units)} files")
```

### Using `stream()` - Progressive Updates

**Location**: CLI, web UI, progress tracking

```python
def stream(
    self,
    initial_state: TransmuteState,
    thread_id: str = "default"
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream workflow execution with live updates.
    
    Use when:
    - You want progress updates
    - Building interactive UI
    - Need to display real-time status
    
    Yields:
        Dict with node name and updated state after each node
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Stream yields after EACH node completes
    for step_output in self.graph.stream(initial_state, config):
        yield step_output


# Example usage in CLI
workflow = TransmuteWorkflow(...)
state = TransmuteState(session_id="cli-001", ...)

# Stream execution
for update in workflow.stream(state):
    # update = {"analyze": {state updates}}
    # update = {"plan": {state updates}}
    # update = {"translate": {state updates}}
    # update = {"validate": {state updates}}
    
    for node_name, node_updates in update.items():
        print(f"✓ {node_name} completed")
        
        if node_name == "translate":
            # Show progress
            if 'migration_plan' in node_updates:
                plan = node_updates['migration_plan']
                completed = len(plan.get_completed_units())
                total = plan.total_units
                print(f"Progress: {completed}/{total}")
```

### How Streaming Works in the CLI

**Location**: `src/transmute/cli/commands/translate.py`

```python
def translate(repository, target_language, output, max_files, ...):
    """CLI translate command."""
    
    # Initialize workflow
    workflow = TransmuteWorkflow(...)
    
    # Create initial state
    state = TransmuteState(
        session_id=f"cli_{uuid.uuid4().hex[:8]}",
        metadata={'max_files': max_files, 'output_dir': output}
    )
    state.repository = RepositoryMetadata(url=repository, ...)
    state.target_language = LanguageInfo(name=target_language)
    
    # Track final state
    current_state = state
    
    # Stream workflow with progress bar
    with create_progress() as progress:
        task = progress.add_task("[cyan]Translating...", total=100)
        
        # Each iteration = one node completion
        for step_output in workflow.stream(state, thread_id="cli"):
            # step_output = {node_name: updates_dict}
            
            for node_name, updates in step_output.items():
                # Apply updates to current state
                for key, value in updates.items():
                    if hasattr(current_state, key):
                        setattr(current_state, key, value)
                
                # Update progress bar
                if node_name == "translate":
                    if hasattr(current_state, 'migration_plan'):
                        plan = current_state.migration_plan
                        if plan:
                            total = len(plan.translation_units)
                            completed = sum(
                                1 for u in plan.translation_units
                                if u.status == "completed"
                            )
                            percent = (completed / total * 100) if total > 0 else 0
                            progress.update(task, completed=percent)
        
        # Mark complete
        progress.update(task, completed=100)
    
    # Display results from final state
    if current_state.migration_plan:
        show_results(current_state.migration_plan)
```

### Stream Output Format

**Each stream iteration yields:**

```python
{
    "node_name": {
        "source_language": LanguageInfo(...),
        "feature_profile": FeatureProfile(...),
        "metadata": {...},
        "current_step": "planning"
    }
}
```

**Complete stream sequence:**

```python
# Iteration 1: Analysis completes
{
    "analyze": {
        "source_language": LanguageInfo(name="python"),
        "feature_profile": FeatureProfile(...),
        "metadata": {"file_map": {...}, "clone_path": "..."},
        "current_step": "planning"
    }
}

# Iteration 2: Planning completes
{
    "plan": {
        "migration_plan": MigrationPlan(...),
        "current_step": "translation"
    }
}

# Iteration 3: Translation completes
{
    "translate": {
        "migration_plan": MigrationPlan(...),  # Updated with translations
        "current_step": "validation"
    }
}

# Iteration 4: Validation completes
{
    "validate": {
        "validation_results": [ValidationResult(...)],
        "current_step": "complete"
    }
}
```

## Complete Example

### Full Workflow Execution Trace

```python
# 1. Initialize
workflow = TransmuteWorkflow(
    registry=LanguageRegistry(),
    rag_system=RAGSystem(),
    claude_client=ClaudeClient()
)

# 2. Create initial state
state = TransmuteState(
    session_id="demo-001",
    repository=RepositoryMetadata(
        url="https://github.com/user/python-app",
        platform="github",
        branch="main"
    ),
    target_language=LanguageInfo(name="java"),
    metadata={'max_files': 2}
)

# 3. Stream execution
print("Starting workflow...")

for step_output in workflow.stream(state, thread_id="demo"):
    for node_name, updates in step_output.items():
        print(f"\n{'='*60}")
        print(f"Node: {node_name}")
        print(f"{'='*60}")
        
        if node_name == "analyze":
            print(f"✓ Language detected: {updates.get('source_language').name}")
            print(f"✓ Complexity: {updates.get('feature_profile').complexity_score:.2f}")
            print(f"✓ Files found: {len(updates.get('metadata', {}).get('file_map', {}).get('python', []))}")
        
        elif node_name == "plan":
            plan = updates.get('migration_plan')
            print(f"✓ Strategy selected: {plan.overall_strategy.value}")
            print(f"✓ Units to translate: {plan.total_units}")
        
        elif node_name == "translate":
            plan = updates.get('migration_plan')
            completed = len(plan.get_completed_units())
            print(f"✓ Translations complete: {completed}/{plan.total_units}")
            for unit in plan.get_completed_units():
                print(f"  • {unit.source_path}: {unit.confidence_score:.0%} confidence")
        
        elif node_name == "validate":
            results = updates.get('validation_results', [])
            avg_quality = sum(r.quality_score for r in results) / len(results)
            print(f"✓ Validation complete")
            print(f"✓ Average quality: {avg_quality:.2f}")

print("\n✅ Workflow complete!")
```

**Output:**

```
Starting workflow...

============================================================
Node: analyze
============================================================
✓ Language detected: python
✓ Complexity: 0.43
✓ Files found: 68

============================================================
Node: plan
============================================================
✓ Strategy selected: pattern
✓ Units to translate: 2

============================================================
Node: translate
============================================================
✓ Translations complete: 2/2
  • patterns/dependency_injection.py: 92% confidence
  • patterns/__init__.py: 100% confidence

============================================================
Node: validate
============================================================
✓ Validation complete
✓ Average quality: 0.96

✅ Workflow complete!
```

## Error Handling

### Retry Logic

**Location**: Wrapped around agent calls

```python
# In node method
updates = self.retry_handler.execute_with_retry(
    func=lambda: self.translation_agent(state),
    operation_name="translation",
    fallback=lambda: self._fallback_translation(state)
)
```

**Retry behavior:**
- Max retries: 3
- Delay: 2s, 4s, 8s (exponential backoff)
- Max delay: 30s
- Retryable: API errors, timeouts, rate limits
- Non-retryable: Auth errors, invalid input

### Fallback Translation

```python
def _fallback_translation(self, state: TransmuteState) -> Dict[str, Any]:
    """
    Fallback when LLM translation fails.
    
    Creates placeholder translation without API call.
    """
    plan = state.migration_plan
    pending = plan.get_pending_units()
    
    for unit in pending:
        unit.translated_code = f"// TODO: Translation failed\n{unit.source_code}"
        unit.confidence_score = 0.0
        unit.mark_failed("LLM translation unavailable")
    
    return {
        "migration_plan": plan,
        "current_step": "validation"
    }
```

### Error Propagation

```python
try:
    updates = agent(state)
except Exception as e:
    logger.error(f"Agent failed: {e}")
    
    # Add error to state
    return {
        "errors": state.errors + [str(e)],
        "current_step": "error"
    }
```

## Performance Considerations

### Parallel Processing (Future)

Currently sequential, but can be made parallel:

```python
# Future: Parallel translation
async def _translate_batch(self, units: List[TranslationUnit]):
    tasks = [self._translate_unit(unit) for unit in units]
    results = await asyncio.gather(*tasks)
    return results
```

### State Size Management

**Best Practices:**
- Don't store large data in state
- Use references (file paths) instead of content
- Clean up temporary data after use

```python
# ❌ Bad - stores all file contents in state
state.metadata['file_contents'] = {path: read_file(path) for path in files}

# ✅ Good - stores only paths
state.metadata['file_paths'] = [str(path) for path in files]
```

### Checkpointing

LangGraph saves state after each node:
- Allows recovery from failures
- Enables pause/resume
- Supports branching workflows

```python
# Graph compiled with checkpointer
graph = StateGraph(TransmuteState).compile(
    checkpointer=MemorySaver()
)

# Resume from checkpoint
final_state = graph.invoke(
    initial_state,
    config={"configurable": {"thread_id": "session-123"}}
)
```

## Summary

### Key Takeaways

1. **LangGraph orchestrates** - Manages state flow between agents
2. **Agents are independent** - Only communicate via state
3. **State is immutable** - Agents return updates, don't modify directly
4. **Nodes wrap agents** - Add retry, middleware, logging
5. **Stream for progress** - Use `stream()` for live updates
6. **Invoke for results** - Use `invoke()` for final state only

### Workflow Pattern

```
Initialize → Build Graph → Execute → Handle Updates → Display Results
     ↓           ↓            ↓            ↓              ↓
  Agents     Add Nodes    stream()/   Apply to      Show to
  Created    + Edges      invoke()     State         User
```

---

**Author**: Mohammed Oussiddi  
**Email**: oussiddi.m@gmail.com  
**Last Updated**: December 2025