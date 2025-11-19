import time
import threading
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Dict, Any, Set
from jinja2 import Template

from ..parser.dsl_parser import WorkflowGraph
from ..memory.memory import GlobalMemory
from ..nodes import create_node

class WorkflowEngine:
    def __init__(self, graph: WorkflowGraph, global_memory: GlobalMemory):
        self.graph = graph
        self.memory = global_memory
        self.completed_nodes: Set[str] = set()
        self.skipped_nodes: Set[str] = set()
        self.lock = threading.Lock()

    def _resolve_inputs(self, inputs_config: Dict[str, Any]) -> Dict[str, Any]:
        resolved = {}
        context = self.memory.to_dict()
        
        for key, value in inputs_config.items():
            if isinstance(value, str) and "{{" in value:
                # Simple Jinja2 templating
                try:
                    template = Template(value)
                    resolved[key] = template.render(**context)
                except Exception as e:
                    print(f"Error rendering template {value}: {e}")
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved

    def _check_condition(self, condition: str) -> bool:
        if not condition:
            return True
        
        context = self.memory.to_dict()
        try:
            # Use Jinja2 to render the condition string first
            # e.g. "{{ intent_classifier.category == 'technical_issue' }}" -> "True" or "False"
            template = Template(condition)
            rendered = template.render(**context)
            
            # Python's eval to check boolean
            return eval(rendered)
        except Exception as e:
            print(f"Condition evaluation failed: {condition} -> {e}")
            return False

    def run(self):
        nodes_to_run = set(self.graph.nodes.keys())
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            
            while len(self.completed_nodes) + len(self.skipped_nodes) < len(nodes_to_run):
                # Find ready nodes
                ready_nodes = []
                nodes_to_skip = []

                with self.lock:
                    for node_id in nodes_to_run:
                        if node_id in self.completed_nodes or node_id in self.skipped_nodes:
                            continue
                        if node_id in futures:
                            continue
                        
                        deps = self.graph.dependencies.get(node_id, set())
                        
                        # Check if dependencies are met (either completed or skipped)
                        # If any dependency is SKIPPED, this node should also be SKIPPED (propagation)
                        # UNLESS we want to support "join" logic where only one branch is needed.
                        # For now, let's assume strict dependency: if dep is skipped, I am skipped.
                        
                        deps_completed = deps.issubset(self.completed_nodes)
                        deps_skipped = deps.issubset(self.skipped_nodes)
                        deps_all_finished = deps.issubset(self.completed_nodes.union(self.skipped_nodes))

                        if deps_all_finished:
                            if deps and deps_skipped:
                                # All dependencies skipped -> Propagate skip
                                nodes_to_skip.append(node_id)
                            else:
                                # At least one dependency completed (and others skipped) OR No dependencies -> Run
                                ready_nodes.append(node_id)
                
                # Process skipped nodes immediately
                if nodes_to_skip:
                    with self.lock:
                        for node_id in nodes_to_skip:
                            self.skipped_nodes.add(node_id)
                            print(f"Node {node_id} SKIPPED (dependency skipped).")
                    continue

                if not ready_nodes and not futures and (len(self.completed_nodes) + len(self.skipped_nodes) < len(nodes_to_run)):
                    raise RuntimeError("Deadlock detected! Cycle in graph or missing dependencies.")

                # Submit ready nodes
                for node_id in ready_nodes:
                    node_config = self.graph.nodes[node_id]
                    
                    # Check Condition
                    condition = node_config.get("condition")
                    if condition and not self._check_condition(condition):
                        with self.lock:
                            self.skipped_nodes.add(node_id)
                        print(f"Node {node_id} SKIPPED (condition false).")
                        continue

                    print(f"Submitting node: {node_id}")
                    node_type = node_config.get("type")
                    
                    # Resolve inputs just before execution
                    inputs = self._resolve_inputs(node_config.get("inputs", {}))
                    
                    node_instance = create_node(node_id, node_type, node_config)
                    future = executor.submit(node_instance.run, inputs)
                    futures[node_id] = future

                # Wait for at least one to finish
                if futures:
                    done, _ = wait(list(futures.values()), return_when="FIRST_COMPLETED")
                    
                    for node_id, future in list(futures.items()):
                        if future in done:
                            try:
                                result = future.result()
                                self.memory.set(node_id, result)
                                with self.lock:
                                    self.completed_nodes.add(node_id)
                                del futures[node_id]
                                print(f"Node {node_id} completed.")
                            except Exception as e:
                                print(f"Node {node_id} failed: {e}")
                                raise e
                else:
                    time.sleep(0.1)

        print("Workflow execution completed.")
