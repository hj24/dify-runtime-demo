from .simple import SleepNode, PrintNode, MathNode, IntentClassifierNode, RouterNode, MockSearchNode as SimpleMockSearchNode
from .llm import LLMNode, MockSearchNode, FormatNode

NODE_CLASSES = {
    "sleep": SleepNode,
    "print": PrintNode,
    "math": MathNode,
    "llm": LLMNode,
    "mock_search": SimpleMockSearchNode, # Use the one from simple.py for this demo
    "format": FormatNode,
    "intent_classifier": IntentClassifierNode,
    "router": RouterNode,
}

def create_node(node_id: str, node_type: str, config: dict):
    node_cls = NODE_CLASSES.get(node_type)
    if not node_cls:
        raise ValueError(f"Unknown node type: {node_type}")
    return node_cls(node_id, config)
