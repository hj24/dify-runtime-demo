from typing import List, Dict, Any
from ..db.db import SessionLocal, Conversation, Message

class ConversationMemory:
    def __init__(self, conversation_id: str, user_id: str = None):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.session = SessionLocal()
        self._ensure_conversation()

    def _ensure_conversation(self):
        conv = self.session.query(Conversation).filter_by(id=self.conversation_id).first()
        if not conv:
            conv = Conversation(id=self.conversation_id, user_id=self.user_id)
            self.session.add(conv)
            self.session.commit()

    def add_message(self, role: str, content: str):
        msg = Message(conversation_id=self.conversation_id, role=role, content=content)
        self.session.add(msg)
        self.session.commit()

    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        # Simple history retrieval
        # msgs = self.session.query(Message).filter_by(conversation_id=self.conversation_id)\
        #     .order_by(Message.id).all() # Should order by created_at in real app
        
        msgs = self.session.query(Message).order_by(Message.id).all()
        
        # Take last N
        msgs = msgs[-limit:]
        
        return [{"role": m.role, "content": m.content} for m in msgs]

    def get_history_str(self, limit: int = 10) -> str:
        history = self.get_history(limit)
        return "\n".join([f"{m['role']}: {m['content']}" for m in history])

    def close(self):
        self.session.close()
