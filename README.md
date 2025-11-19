# Dify Runtime Demo 文档

本文档总结了当前的 DSL (Domain Specific Language) 定义与 Runtime (运行时) 实现细节。

## 1. Agent 命令调用 (Usage)

可以通过命令行工具 `runtime/main.py` 来执行 Workflow。

### 基本用法

```bash
# 运行默认示例
python3 -m runtime.main --file dsl/vnext/demo.yaml

# 运行不带数据库持久化的版本 (用于测试)
python3 -m runtime.main --file dsl/vnext/demo.yaml --no-db

# 运行交互式对话模式 (Chat Mode)
python3 -m runtime.main --file dsl/vnext/aws_support.yaml --chat --no-db
```

### 参数说明

- `--file <path>`: 指定要运行的 DSL 文件路径 (YAML 格式)。
- `--no-db`: 禁用数据库持久化，仅在内存中运行。
- `--chat`: 启动交互式对话模式 (CLI Chat Loop)。

---

## 2. DSL 文档 (DSL Specification)

DSL 使用 YAML 格式定义 Workflow 的结构、节点及其依赖关系。

### 核心结构

一个标准的 DSL 文件包含以下部分：

```yaml
version: "4.0-dataflow"  # DSL 版本号
name: "Workflow Name"    # 工作流名称
start: "start_node_id"   # (可选) 起始节点，通常由依赖关系自动推导

inputs:                  # 全局输入定义
  query: string
  user_id: string

nodes:                   # 节点定义集合
  node_id_1:
    type: node_type      # 节点类型 (e.g., llm, router, print)
    inputs:              # 节点输入参数
      param1: "value"
      param2: "{{ inputs.query }}" # 支持 Jinja2 模板引用
    next: [node_id_2]    # (可选) 显式指定后续节点
    depends_on: []       # (可选) 显式指定依赖节点
    condition: "{{ ... }}" # (可选) 执行条件
    end: true            # (可选) 标记为结束节点
```

### 关键特性

1.  **节点引用 (Templating)**: 使用 Jinja2 语法 `{{ node_id.output_field }}` 引用其他节点的输出或全局输入。
2.  **隐式依赖 (Implicit Dependency)**: Runtime 会解析 `inputs` 中的引用，自动建立节点间的依赖关系。
3.  **显式依赖 (Explicit Dependency)**: 使用 `depends_on` 强制指定执行顺序（例如无数据依赖但需按序执行）。
4.  **条件执行 (Conditional Execution)**: `condition` 字段支持 Python 表达式 (基于 Jinja2 渲染结果)，用于控制节点是否执行。
5.  **并行执行 (Parallelism)**: 无依赖关系的节点会被 Runtime 自动并行执行。

### 示例

```yaml
nodes:
  # 意图分类节点
  intent_classifier:
    type: llm
    inputs:
      prompt: "Classify: {{ inputs.query }}"
  
  # 路由节点
  router:
    type: router
    inputs:
      intent: "{{ intent_classifier.text }}"
    next: [search_node, reply_node] # 分支

  # 搜索节点 (仅在特定条件下执行)
  search_node:
    type: mock_search
    condition: "{{ 'technical' in intent_classifier.text }}"
    inputs:
      query: "{{ inputs.query }}"
```

---

## 3. Runtime 实现 (Runtime Architecture)

Runtime 负责解析 DSL 并调度节点的执行。它采用了 **基于数据的自动并行调度 (Data-Driven Parallel Scheduling)** 机制。

### 架构图 (Architecture Diagram)

![Runtime Architecture](https://mermaid.ink/img/Z3JhcGggVEQKICAgIENMSVtDTEkgLyBBUEldIC0tPiBQYXJzZXJbRFNMIFBhcnNlcl0KICAgIFBhcnNlciAtLT58V29ya2Zsb3dHcmFwaHwgRW5naW5lW1dvcmtmbG93IEVuZ2luZV0KICAgIAogICAgc3ViZ3JhcGggUnVudGltZV9Db3JlIFtSdW50aW1lIENvcmVdCiAgICAgICAgZGlyZWN0aW9uIFRCCiAgICAgICAgRW5naW5lIC0tPnxJbml0fCBNZW1vcnlbR2xvYmFsIE1lbW9yeV0KICAgICAgICAKICAgICAgICBzdWJncmFwaCBTY2hlZHVsZXIgW1NjaGVkdWxlciBMb29wXQogICAgICAgICAgICBkaXJlY3Rpb24gVEIKICAgICAgICAgICAgQ2hlY2tbRGVwZW5kZW5jeSBDaGVja10KICAgICAgICAgICAgU3VibWl0W1N1Ym1pdCBUYXNrc10KICAgICAgICAgICAgV2FpdFtXYWl0IGZvciBFdmVudF0KICAgICAgICAgICAgVXBkYXRlW1VwZGF0ZSBTdGF0ZV0KICAgICAgICAgICAgCiAgICAgICAgICAgIENoZWNrIC0tPnxSZWFkeXwgU3VibWl0CiAgICAgICAgICAgIENoZWNrIC0tPnxTa2lwcGVkfCBVcGRhdGUKICAgICAgICAgICAgU3VibWl0IC0tPnxGdXR1cmV8IFdhaXQKICAgICAgICAgICAgV2FpdCAtLT58Tm9kZSBGaW5pc2hlZHwgVXBkYXRlCiAgICAgICAgICAgIFVwZGF0ZSAtLT4gQ2hlY2sKICAgICAgICBlbmQKICAgICAgICAKICAgICAgICBFbmdpbmUgLS0+IENoZWNrCiAgICAgICAgCiAgICAgICAgU3VibWl0IC0tPiBFeGVjdXRvcltUaHJlYWRQb29sIEV4ZWN1dG9yXQogICAgICAgIAogICAgICAgIEV4ZWN1dG9yIC0tPnxBc3luYyBSdW58IE5vZGVbTm9kZSBJbnN0YW5jZV0KICAgICAgICBOb2RlIC0tPnxXcml0ZSBSZXN1bHR8IE1lbW9yeQogICAgZW5k)

### 核心组件

1.  **WorkflowEngine (`runtime/core/engine.py`)**:
    *   核心调度器。
    *   维护 `completed_nodes` 和 `skipped_nodes` 集合。
    *   循环检查所有节点的依赖状态 (`Ready`, `Waiting`, `Skipped`)。
    *   将满足依赖的节点提交给线程池执行。
    *   处理条件逻辑：如果条件不满足，标记节点为 `SKIPPED` 并传播跳过状态。

2.  **GlobalMemory (`runtime/memory/memory.py`)**:
    *   线程安全的全局状态存储。
    *   存储 `inputs` (全局输入) 和所有节点的执行结果。
    *   提供 `get/set` 方法，支持点号路径访问 (e.g., `node_a.result`)。

3.  **DSL Parser (`runtime/parser/dsl_parser.py`)**:
    *   解析 YAML 文件。
    *   提取显式依赖 (`depends_on`) 和隐式依赖 (正则匹配 `{{ node.field }}`)。
    *   构建 `WorkflowGraph` 对象，包含节点配置和依赖拓扑。

4.  **Node System (`runtime/nodes/`)**:
    *   定义了 `Node` 基类和具体实现 (e.g., `LLMNode`, `RouterNode`).
    *   每个节点独立执行，接收 `inputs`，返回字典结果。

### 4. 调度算法详解 (Scheduling Algorithm Detail)

Runtime 的调度核心维护了一个状态循环，确保节点按正确的依赖顺序和并行度执行。

#### 状态管理
每个节点在生命周期中会处于以下状态之一：
- **PENDING**: 初始状态，等待依赖满足。
- **READY**: 所有依赖已完成 (Completed)，准备提交执行。
- **RUNNING**: 正在线程池中执行。
- **COMPLETED**: 执行成功，结果已写入 Global Memory。
- **SKIPPED**: 因依赖被跳过或条件 (Condition) 不满足而被跳过。

#### 调度循环 (Scheduling Loop)
`WorkflowEngine.run()` 方法的主循环逻辑如下：

1.  **检测依赖 (Dependency Check)**:
    *   遍历所有未完成 (Non-Terminal) 的节点。
    *   **Propagation (跳过传播)**: 如果某节点的 *任意* 前置依赖节点处于 `SKIPPED` 状态，则该节点立即标记为 `SKIPPED`。
    *   **Activation (激活)**: 如果某节点的 *所有* 前置依赖节点都处于 `COMPLETED` 状态，则该节点标记为 `READY`。

2.  **提交任务 (Submission)**:
    *   将所有 `READY` 状态的节点提交给 `ThreadPoolExecutor`。
    *   在提交前进行 **条件求值 (Condition Evaluation)**:
        *   渲染 `condition` 模板 (e.g., `{{ inputs.val > 10 }}`)。
        *   如果结果为 `False`，不提交任务，直接将节点标记为 `SKIPPED`。
        *   如果结果为 `True` (或无条件)，则正式提交执行。

3.  **等待与回调 (Wait & Callback)**:
    *   主线程使用 `wait(return_when=FIRST_COMPLETED)` 阻塞，直到至少一个节点执行完毕。
    *   一旦有节点完成，更新 `completed_nodes` 集合和 `Global Memory`。
    *   循环回到第 1 步，检查是否有新的节点满足了依赖 (被刚刚完成的节点解锁)。

4.  **死锁检测 (Deadlock Detection)**:
    *   如果当前没有正在运行的节点，且仍有未完成的节点，但没有任何节点变为 `READY`，则判定为死锁 (通常由循环依赖导致)，抛出异常。


### 执行流程

1.  **初始化**: 加载 DSL，解析为图，初始化 Global Memory。
2.  **调度循环**:
    *   扫描所有未完成节点。
    *   检查依赖：
        *   如果所有依赖节点已完成 -> **Ready** (加入执行队列)。
        *   如果任一依赖节点被跳过 (Skipped) -> **Skip** (标记当前节点为 Skipped)。
        *   否则 -> **Wait**。
3.  **执行**:
    *   解析节点输入 (渲染 Jinja2 模板)。
    *   检查 `condition`。若为 False，标记 Skipped。
    *   在线程池中异步执行节点逻辑。
4.  **结果回写**: 节点执行完成后，结果写入 Global Memory，触发后续节点解锁。
5.  **结束**: 当所有节点都处于 Completed 或 Skipped 状态时，工作流结束。
