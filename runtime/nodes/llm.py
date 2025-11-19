import os
from openai import OpenAI
from .simple import BaseNode

class LLMNode(BaseNode):
    def run(self, inputs: dict) -> dict:
        model = inputs.get("model", "gpt-4o")
        prompt = inputs.get("prompt", "")
        temperature = float(inputs.get("temperature", 0.7))
        max_tokens = int(inputs.get("max_tokens", 1000))
        
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Get base_url from environment variable
        # This supports:
        # - OpenAI proxies/mirrors
        # - Azure OpenAI endpoints
        # - Local model servers (vLLM, Ollama, LM Studio, etc.)
        base_url = os.getenv("OPENAI_BASE_URL")
        
        # Initialize OpenAI client with optional base_url
        if base_url:
            client = OpenAI(api_key=api_key, base_url=base_url)
            print(f"[{self.node_id}] Using custom base_url: {base_url}")
        else:
            client = OpenAI(api_key=api_key)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.node_id}] Calling OpenAI {model}...")
        print(f"[{timestamp}] [{self.node_id}] Prompt: {prompt[:100]}...")
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            text = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        except Exception as e:
            print(f"[{self.node_id}] OpenAI API call failed: {e}")
            print(f"[{self.node_id}] Falling back to MOCK response.")
            text = f"[MOCK LLM RESPONSE] Based on the search results, here is the solution for your '{model}' query.\n\n(Real API call failed, this is a simulation.)"
            usage = {"total_tokens": 0}
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.node_id}] Response: {text[:100]}...")
        print(f"[{timestamp}] [{self.node_id}] Tokens used: {usage['total_tokens']}")
        
        return {
            "text": text,
            "usage": usage,
            "model": model
        }

class MockSearchNode(BaseNode):
    def run(self, inputs: dict) -> dict:
        keywords = inputs.get("keywords", "")
        print(f"[{self.node_id}] Simulating search for: {keywords}")
        
        # Mock search results
        results = f"Found information related to: {keywords}"
        sources = "Wikipedia, arXiv, Stack Overflow"
        
        return {
            "results": results,
            "sources": sources,
            "keyword_count": len(keywords.split(","))
        }

class FormatNode(BaseNode):
    def run(self, inputs: dict) -> dict:
        template = inputs.get("template", "{{ text }}")
        print(f"[{self.node_id}] Formatting output...")
        
        # Simple template rendering (already done by engine)
        # Just pass through
        return {
            "formatted": template,
            "length": len(template)
        }
