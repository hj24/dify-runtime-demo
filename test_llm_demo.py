#!/usr/bin/env python3
"""
Test script for the Intelligent QA Demo
Demonstrates memory flow between LLM nodes
"""

import sys
import os

# Add runtime to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from runtime.main import main

if __name__ == "__main__":
    # Override sys.argv to pass custom arguments
    sys.argv = [
        "test_llm_demo.py",
        "--file", "dsl/vnext/intelligent_qa.yaml",
        "--no-db"  # Skip DB for quick testing
    ]
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("=" * 60)
        print("WARNING: OPENAI_API_KEY not set!")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        print("=" * 60)
        sys.exit(1)
    
    print("=" * 60)
    print("INTELLIGENT QA DEMO - Testing Memory Flow")
    print("=" * 60)
    print()
    
    main()
