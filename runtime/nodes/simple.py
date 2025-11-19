import time
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseNode(ABC):
    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config

    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Any:
        pass

class SleepNode(BaseNode):
    def run(self, inputs: Dict[str, Any]) -> Any:
        duration = float(inputs.get("duration", 1))
        print(f"[{self.node_id}] Sleeping for {duration} seconds...")
        time.sleep(duration)
        print(f"[{self.node_id}] Woke up!")
        return {"status": "slept", "duration": duration}

class PrintNode(BaseNode):
    def run(self, inputs: Dict[str, Any]) -> Any:
        message = inputs.get("message", "")
        print(f"[{self.node_id}] OUTPUT: {message}")
        return {"printed": message}

class MathNode(BaseNode):
    def run(self, inputs: Dict[str, Any]) -> Any:
        a = float(inputs.get("a", 0))
        b = float(inputs.get("b", 0))
        op = inputs.get("op", "add")
        
        if op == "add":
            result = a + b
        elif op == "sub":
            result = a - b
        elif op == "mul":
            result = a * b
        else:
            result = 0
            
        print(f"[{self.node_id}] Math: {a} {op} {b} = {result}")
        return {"result": result}



class IntentClassifierNode(BaseNode):
    def run(self, inputs: Dict[str, Any]) -> Any:
        query = inputs.get("query", "").lower()
        categories = inputs.get("categories", [])
        
        # Simple rule-based classification for demo
        if "ec2" in query or "server" in query or "down" in query:
            category = "technical_issue"
        elif "bill" in query or "cost" in query:
            category = "billing"
        else:
            category = "general_inquiry"
            
        print(f"[{self.node_id}] Classified '{query}' as '{category}'")
        return {"category": category}

class RouterNode(BaseNode):
    def run(self, inputs: Dict[str, Any]) -> Any:
        # Router just passes through, the branching happens in next nodes' conditions
        intent = inputs.get("intent")
        print(f"[{self.node_id}] Routing based on intent: {intent}")
        return {"intent": intent}

class MockSearchNode(BaseNode):
    def run(self, inputs: Dict[str, Any]) -> Any:
        query = inputs.get("query", "")
        source = inputs.get("source", "unknown")
        duration = float(inputs.get("duration", 0.5))
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.node_id}] Searching {source} for '{query}' (taking {duration}s)...")
        time.sleep(duration)
        
        # Mock results
        if source == "official_docs":
            results = "Official Docs: EC2 instance troubleshooting guide. Check security groups."
        elif source == "community_forum":
            results = "Community Forum: User 'cloud_guru' suggests restarting the instance."
        else:
            results = "No results found."
            
        return {"results": results}

NODE_CLASSES = {
    "sleep": SleepNode,
    "print": PrintNode,
    "math": MathNode,
    "intent_classifier": IntentClassifierNode,
    "router": RouterNode,
    "mock_search": MockSearchNode,
    "llm": PrintNode, # Fallback LLM to Print for now if no API key, or we can use a MockLLM
}

def create_node(node_id: str, node_type: str, config: Dict[str, Any]) -> BaseNode:
    node_cls = NODE_CLASSES.get(node_type)
    if not node_cls:
        raise ValueError(f"Unknown node type: {node_type}")
    return node_cls(node_id, config)
