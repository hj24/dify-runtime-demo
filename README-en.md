# Dify Runtime Demo Documentation

This document summarizes the current DSL (Domain Specific Language) definition and Runtime implementation details.

## 1. Usage

You can execute the Workflow using the command-line tool `runtime/main.py`.

### Basic Usage

```bash
# Run the default demo
python3 -m runtime.main --file dsl/vnext/demo.yaml

# Run without database persistence (for testing)
python3 -m runtime.main --file dsl/vnext/demo.yaml --no-db

# Run in interactive chat mode
python3 -m runtime.main --file dsl/vnext/aws_support.yaml --chat --no-db
```

### Arguments

- `--file <path>`: Specify the DSL file path to run (YAML format).
- `--no-db`: Disable database persistence, run in memory only.
- `--chat`: Start interactive chat mode (CLI Chat Loop).

---

## 2. DSL Specification

The DSL uses YAML format to define the structure of the Workflow, its nodes, and their dependencies.

### Core Structure

A standard DSL file contains the following parts:

```yaml
version: "4.0-dataflow"  # DSL Version
name: "Workflow Name"    # Workflow Name
start: "start_node_id"   # (Optional) Start node, usually inferred from dependencies

inputs:                  # Global Input Definition
  query: string
  user_id: string

nodes:                   # Node Definitions
  node_id_1:
    type: node_type      # Node Type (e.g., llm, router, print)
    inputs:              # Node Inputs
      param1: "value"
      param2: "{{ inputs.query }}" # Supports Jinja2 templating
    next: [node_id_2]    # (Optional) Explicitly specify next nodes
    depends_on: []       # (Optional) Explicitly specify dependencies
    condition: "{{ ... }}" # (Optional) Execution condition
    end: true            # (Optional) Mark as end node
```

### Key Features

1.  **Templating**: Use Jinja2 syntax `{{ node_id.output_field }}` to reference outputs of other nodes or global inputs.
2.  **Implicit Dependency**: The Runtime parses references in `inputs` to automatically establish dependencies between nodes.
3.  **Explicit Dependency**: Use `depends_on` to enforce execution order (e.g., when there is no data dependency but order matters).
4.  **Conditional Execution**: The `condition` field supports Python expressions (based on Jinja2 rendered results) to control whether a node executes.
5.  **Parallelism**: Nodes with no dependencies are automatically executed in parallel by the Runtime.

### Example

```yaml
nodes:
  # Intent Classifier Node
  intent_classifier:
    type: llm
    inputs:
      prompt: "Classify: {{ inputs.query }}"
  
  # Router Node
  router:
    type: router
    inputs:
      intent: "{{ intent_classifier.text }}"
    next: [search_node, reply_node] # Branches

  # Search Node (Executes only under specific conditions)
  search_node:
    type: mock_search
    condition: "{{ 'technical' in intent_classifier.text }}"
    inputs:
      query: "{{ inputs.query }}"
```

---

## 3. Runtime Architecture

The Runtime is responsible for parsing the DSL and scheduling node execution. It employs a **Data-Driven Parallel Scheduling** mechanism.

### Architecture Diagram

![Runtime Architecture](https://mermaid.ink/img/Z3JhcGggVEQKICAgIENMSVtDTEkgLyBBUEldIC0tPiBQYXJzZXJbRFNMIFBhcnNlcl0KICAgIFBhcnNlciAtLT58V29ya2Zsb3dHcmFwaHwgRW5naW5lW1dvcmtmbG93IEVuZ2luZV0KICAgIAogICAgc3ViZ3JhcGggUnVudGltZSBDb3JlCiAgICAgICAgRW5naW5lIC0tPnxSZWFkL1dyaXRlfCBNZW1vcnlbR2xvYmFsIE1lbW9yeV0KICAgICAgICBFbmdpbmUgLS0+fFN1Ym1pdCBUYXNrc3wgRXhlY3V0b3JbVGhyZWFkUG9vbCBFeGVjdXRvcl0KICAgICAgICAKICAgICAgICBFeGVjdXRvciAtLT58UnVufCBOb2RlQVtOb2RlIEluc3RhbmNlIEFdCiAgICAgICAgRXhlY3V0b3IgLS0+fFJ1bnwgTm9kZUJbTm9kZSBJbnN0YW5jZSBCXQogICAgICAgIAogICAgICAgIE5vZGVBIC0tPnxSZXN1bHR8IE1lbW9yeQogICAgICAgIE5vZGVCIC0tPnxSZXN1bHR8IE1lbW9yeQogICAgZW5kCiAgICAKICAgIE1lbW9yeSAtLi0+fENvbnRleHR8IE5vZGVBCiAgICBNZW1vcnkgLS4tPnxDb250ZXh0fCBOb2RlQg==)

### Core Components

1.  **WorkflowEngine (`runtime/core/engine.py`)**:
    *   The core scheduler.
    *   Maintains `completed_nodes` and `skipped_nodes` sets.
    *   Loops to check the dependency status of all nodes (`Ready`, `Waiting`, `Skipped`).
    *   Submits nodes that satisfy dependencies to the thread pool for execution.
    *   Handles conditional logic: if a condition is not met, marks the node as `SKIPPED` and propagates the skip status.

2.  **GlobalMemory (`runtime/memory/memory.py`)**:
    *   Thread-safe global state storage.
    *   Stores `inputs` (global inputs) and execution results of all nodes.
    *   Provides `get/set` methods, supporting dot notation access (e.g., `node_a.result`).

3.  **DSL Parser (`runtime/parser/dsl_parser.py`)**:
    *   Parses YAML files.
    *   Extracts explicit dependencies (`depends_on`) and implicit dependencies (regex matching `{{ node.field }}`).
    *   Constructs the `WorkflowGraph` object, containing node configurations and dependency topology.

4.  **Node System (`runtime/nodes/`)**:
    *   Defines the `Node` base class and concrete implementations (e.g., `LLMNode`, `RouterNode`).
    *   Each node executes independently, receiving `inputs` and returning a dictionary result.

### Execution Flow

1.  **Initialization**: Load DSL, parse into a graph, initialize Global Memory.
2.  **Scheduling Loop**:
    *   Scan all incomplete nodes.
    *   Check dependencies:
        *   If all dependencies are completed -> **Ready** (Add to execution queue).
        *   If any dependency is skipped -> **Skip** (Mark current node as Skipped).
        *   Otherwise -> **Wait**.
3.  **Execution**:
    *   Resolve node inputs (render Jinja2 templates).
    *   Check `condition`. If False, mark as Skipped.
    *   Execute node logic asynchronously in the thread pool.
4.  **Result Write-back**: After node execution completes, results are written to Global Memory, triggering the unlocking of subsequent nodes.
5.  **Termination**: The workflow ends when all nodes are in either Completed or Skipped state.
