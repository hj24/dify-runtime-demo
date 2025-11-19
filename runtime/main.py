import argparse
import json
import time
import uuid
from dotenv import load_dotenv

load_dotenv()

from .db.db import init_db, SessionLocal, Workflow, WorkflowRun
from .parser.dsl_parser import parse_workflow
from .core.engine import WorkflowEngine
from .memory.memory import GlobalMemory
from .memory.conversation import ConversationMemory

def run_single_execution(graph, args, session, workflow_id):
    # Determine inputs based on workflow
    if graph.workflow_id == "intelligent_qa_demo":
        initial_inputs = {
            "inputs": {
                "question": "What is the difference between supervised and unsupervised machine learning?"
            }
        }
    else:
        # Default inputs for basic demo
        initial_inputs = {
            "inputs": {
                "query": "Hello Dify vNext",
                "a": 10,
                "b": 20
            }
        }
    memory = GlobalMemory(initial_inputs)
    engine = WorkflowEngine(graph, memory)

    # Create Run Record
    run_id = None
    if not args.no_db and workflow_id:
        run = WorkflowRun(workflow_id=workflow_id, status="RUNNING")
        session.add(run)
        session.commit()
        run_id = run.id
        print(f"Created workflow run (ID: {run_id})")

    # Run
    start_time = time.time()
    try:
        engine.run()
        status = "COMPLETED"
    except Exception as e:
        print(f"Execution failed: {e}")
        status = "FAILED"
    
    duration = time.time() - start_time
    print(f"Execution finished in {duration:.2f}s")

    # Update Run Record
    if not args.no_db and run_id:
        run = session.query(WorkflowRun).filter_by(id=run_id).first()
        run.status = status
        run.global_memory = memory.to_dict()
        session.commit()
        print("Updated run record.")

    print("Final Memory State:")
    print(json.dumps(memory.to_dict(), indent=2))

def chat_loop(graph, no_db):
    conversation_id = str(uuid.uuid4())
    print(f"Starting chat session: {conversation_id}")
    print("Type 'exit' to quit.")
    
    memory_manager = None
    if not no_db:
        memory_manager = ConversationMemory(conversation_id)

    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            if memory_manager:
                memory_manager.add_message("user", user_input)
            
            # Prepare inputs
            history_str = ""
            if memory_manager:
                history_str = memory_manager.get_history_str()

            inputs = {
                "inputs": {
                    "query": user_input,
                    "conversation_id": conversation_id,
                    "memory": history_str
                }
            }
            
            # Run Workflow
            memory = GlobalMemory(inputs)
            engine = WorkflowEngine(graph, memory)
            engine.run()
            
            # Get output
            # For AWS bot, 'end_node' has the message.
            final_output = memory.get("end_node")
            response = "..."
            if final_output and isinstance(final_output, dict):
                 response = final_output.get("printed", "...")
            
            print(f"Bot: {response}")
            
            if memory_manager:
                memory_manager.add_message("assistant", response)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Dify vNext Runtime Demo")
    parser.add_argument("--file", type=str, default="dsl/vnext/demo.yaml", help="Path to workflow YAML file")
    parser.add_argument("--no-db", action="store_true", help="Skip database persistence")
    parser.add_argument("--chat", action="store_true", help="Run in interactive chat mode")
    args = parser.parse_args()

    # 1. Init DB
    if not args.no_db:
        try:
            init_db()
            print("Database initialized.")
        except Exception as e:
            print(f"Warning: Database initialization failed ({e}). Running without DB persistence.")
            args.no_db = True

    # 2. Load YAML
    with open(args.file, "r") as f:
        yaml_content = f.read()
    
    print(f"Loaded workflow from {args.file}")

    # 3. Parse DSL
    graph = parse_workflow(yaml_content)
    print(f"=" * 60)
    print(f"Workflow: {graph.workflow_id} (v{graph.version})")
    print(f"=" * 60)

    # 4. Persist Workflow Definition
    session = None
    workflow_id = None
    if not args.no_db:
        session = SessionLocal()
        workflow = Workflow(name="Demo Workflow", dsl_definition=graph.nodes)
        session.add(workflow)
        session.commit()
        workflow_id = workflow.id
        print(f"Persisted workflow definition (ID: {workflow_id})")

    if args.chat:
        chat_loop(graph, args.no_db)
    else:
        run_single_execution(graph, args, session, workflow_id)
        if session:
            session.close()

if __name__ == "__main__":
    main()
