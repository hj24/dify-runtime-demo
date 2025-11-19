from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

from .db.db import init_db
from .parser.dsl_parser import parse_workflow
from .core.engine import WorkflowEngine
from .memory.memory import GlobalMemory
from .memory.conversation import ConversationMemory

app = FastAPI(title="Dify Runtime Demo API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
try:
    init_db()
    print("Database initialized.")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")

# Load Workflow
DSL_PATH = "dsl/vnext/aws_support.yaml"
try:
    with open(DSL_PATH, "r") as f:
        yaml_content = f.read()
    graph = parse_workflow(yaml_content)
    print(f"Loaded workflow from {DSL_PATH}")
except Exception as e:
    print(f"Error loading workflow: {e}")
    graph = None

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    response: str

@app.post("/chat/send", response_model=ChatResponse)
def send_message(req: ChatRequest):
    if not graph:
        raise HTTPException(status_code=500, detail="Workflow not loaded")

    conversation_id = req.conversation_id or str(uuid.uuid4())
    
    # Memory Manager
    memory_manager = ConversationMemory(conversation_id)
    memory_manager.add_message("user", req.query)
    history_str = memory_manager.get_history_str()
    
    # Inputs
    inputs = {
        "inputs": {
            "query": req.query,
            "conversation_id": conversation_id,
            "memory": history_str
        }
    }
    
    # Run
    memory = GlobalMemory(inputs)
    engine = WorkflowEngine(graph, memory)
    
    try:
        # TODO: Capture logs/print output if needed
        engine.run()
    except Exception as e:
        print(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    # Get Output
    # For AWS bot, 'end_node' has the message.
    final_output = memory.get("end_node")
    response_text = "..."
    if final_output and isinstance(final_output, dict):
        response_text = final_output.get("printed", "...")
        
    # Save response
    memory_manager.add_message("assistant", response_text)
    
    return ChatResponse(
        conversation_id=conversation_id,
        response=response_text
    )

@app.get("/chat/history/{conversation_id}")
def get_history(conversation_id: str):
    memory_manager = ConversationMemory(conversation_id)
    return memory_manager.get_history()

class DSLContent(BaseModel):
    content: str

@app.get("/dsl/content")
def get_dsl_content():
    try:
        with open(DSL_PATH, "r") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dsl/content")
def update_dsl_content(dsl: DSLContent):
    global graph
    try:
        # Validate first
        new_graph = parse_workflow(dsl.content)
        
        # Save to file
        with open(DSL_PATH, "w") as f:
            f.write(dsl.content)
            
        # Update global graph
        graph = new_graph
        print(f"Reloaded workflow from {DSL_PATH}")
        
        return {"status": "ok", "message": "DSL updated and reloaded"}
    except Exception as e:
        print(f"Error updating DSL: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid DSL: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "ok", "workflow_loaded": graph is not None}
