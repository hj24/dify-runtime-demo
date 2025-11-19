# Dify Runtime Demo - LLM Memory Flow Example

## Overview

This demo showcases an **Intelligent QA System** that demonstrates how memory flows between LLM nodes in a multi-step workflow.

## Workflow Architecture

The workflow implements a sophisticated question-answering pipeline:

```
Question Input
     |
     v
[extract_keywords] (LLM) ──┬──> [generate_outline] (LLM)
                           └──> [search_context] (Mock Search)
                                      |
                                      v
                              [generate_final_answer] (LLM)
                                      |
                                      v
                              [format_response]
                                      |
                                      v
                                  Final Output
```

### Key Features

1. **Parallel Execution**: `generate_outline` and `search_context` run in parallel after `extract_keywords` completes.
2. **Memory Flow**: Each node's output is stored in global memory and accessible to downstream nodes via `{{ node_id.field }}` syntax.
3. **Dependency Management**: Both explicit (`depends_on`) and implicit (variable references) dependencies are tracked.

## Setup

1. Install dependencies:
   ```bash
   cd dify-runtime-demo
   uv add openai
   ```

2. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

3. Configure database (optional):
   ```bash
   export DB_URL='postgresql://postgres:password@localhost/dsl_demo'
   ```

## Running the Demo

### Quick Test (No Database)
```bash
python test_llm_demo.py
```

### With Database Persistence
```bash
uv run python -m runtime.main --file dsl/vnext/intelligent_qa.yaml
```

### Custom Question
Edit `dsl/vnext/intelligent_qa.yaml` and modify the `inputs` section in runtime/main.py:

```python
initial_inputs = {
    "inputs": {
        "question": "What is machine learning and how does it work?"
    }
}
```

## Expected Output

The demo will:
1. Extract keywords from the question
2. Generate an answer outline (in parallel with context search)
3. Combine all information to create a comprehensive answer
4. Format the final response

You'll see the execution flow, parallel node submissions, and the final memory state showing how data flowed through the pipeline.

## Understanding Memory Management

Global memory is structured as:
```json
{
  "inputs": { "question": "..." },
  "extract_keywords": { "text": "keyword1, keyword2, ...", "usage": {...} },
  "generate_outline": { "text": "1. Point A\n2. Point B", "usage": {...} },
  "search_context": { "results": "...", "sources": "..." },
  "generate_final_answer": { "text": "comprehensive answer", "usage": {...} },
  "format_response": { "formatted": "final output" }
}
```

Each node can reference previous nodes' outputs using Jinja2 templates.
