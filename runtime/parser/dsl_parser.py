import yaml
import re
from typing import Dict, List, Any, Set

class WorkflowGraph:
    def __init__(self, workflow_id: str, version: str, start_node: str, 
                 nodes: Dict[str, Any], dependencies: Dict[str, Set[str]], 
                 execution_order: Dict[str, List[str]]):
        self.workflow_id = workflow_id
        self.version = version
        self.start_node = start_node
        self.nodes = nodes
        self.dependencies = dependencies
        self.execution_order = execution_order  # node_id -> [next_node_ids]

def parse_workflow(yaml_content: str) -> WorkflowGraph:
    data = yaml.safe_load(yaml_content)
    
    workflow_id = data.get("id", "unnamed_workflow")
    version = data.get("version", "1.0")
    start_node = data.get("start")
    nodes_config = data.get("nodes", {})
    
    dependencies: Dict[str, Set[str]] = {}
    execution_order: Dict[str, List[str]] = {}
    
    # Regex to find {{ node_id.field }} patterns
    variable_pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\.[a-zA-Z0-9_]+\s*\}\}")

    for node_id, config in nodes_config.items():
        # 1. Explicit depends_on
        explicit_deps = set(config.get("depends_on", []))
        
        # 2. Implicit dependencies from inputs (variable references)
        inputs = config.get("inputs", {})
        implicit_deps = set()
        
        def find_deps(obj):
            if isinstance(obj, str):
                matches = variable_pattern.findall(obj)
                for match in matches:
                    if match != "inputs" and match in nodes_config:
                        implicit_deps.add(match)
            elif isinstance(obj, dict):
                for v in obj.values():
                    find_deps(v)
            elif isinstance(obj, list):
                for v in obj:
                    find_deps(v)

        find_deps(inputs)
        
        # Merge explicit and implicit
        if node_id not in dependencies:
            dependencies[node_id] = set()
        dependencies[node_id].update(explicit_deps | implicit_deps)
        
        # Parse 'next' for execution order
        next_nodes = config.get("next", [])
        if next_nodes and not isinstance(next_nodes, list):
            next_nodes = [next_nodes]
        execution_order[node_id] = next_nodes
        
        # Convert 'next' to reverse dependencies
        # If A.next = [B], then B depends on A
        for target_node in next_nodes:
            # We need to handle cases where target_node might not be defined yet
            # So we'll do a second pass or use a temporary map
            if target_node not in dependencies:
                dependencies[target_node] = set()
            dependencies[target_node].add(node_id)

    return WorkflowGraph(workflow_id, version, start_node, nodes_config, dependencies, execution_order)
