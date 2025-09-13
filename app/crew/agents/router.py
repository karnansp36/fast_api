# crew/agents/router.py
from crewai import Agent
from app.crew.llm_config import analytical_llm
import logging
from typing import Dict, Any, List
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class IntelligentAgentRouter:
    def __init__(self):
        self.agent_registry = {}
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.agent_embeddings = {}
        self.performance_metrics = {}
        
    def register_agent(self, agent_name: str, description: str, capabilities: List[str], 
                      specialties: List[str], weight: float = 1.0):
        """Register an agent with its capabilities"""
        self.agent_registry[agent_name] = {
            "description": description,
            "capabilities": capabilities,
            "specialties": specialties,
            "weight": weight,
            "usage_count": 0,
            "success_rate": 1.0
        }
        
        # Create embedding for similarity matching
        agent_text = f"{description} {' '.join(capabilities)} {' '.join(specialties)}"
        self.agent_embeddings[agent_name] = self.embedding_model.encode(agent_text)
    
    async def select_best_agent(self, message: str, context: Dict[str, Any]) -> List[str]:
        """Select the most appropriate agent(s) for the message using multiple strategies"""
        # Strategy 1: Semantic similarity
        message_embedding = self.embedding_model.encode(message)
        similarities = {}
        
        for agent_name, agent_embedding in self.agent_embeddings.items():
            similarity = cosine_similarity([message_embedding], [agent_embedding])[0][0]
            # Adjust by agent weight and performance
            adjusted_similarity = similarity * self.agent_registry[agent_name]["weight"] * self.agent_registry[agent_name]["success_rate"]
            similarities[agent_name] = adjusted_similarity
        
        # Get top 3 agents by similarity
        top_agents = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Strategy 2: Rule-based fallback for certain patterns
        rule_based_agents = self._rule_based_selection(message)
        
        # Combine strategies
        final_selection = list(set([agent[0] for agent in top_agents] + rule_based_agents))
        
        return final_selection
    
    def _rule_based_selection(self, message: str) -> List[str]:
        """Rule-based fallback for certain message patterns"""
        message_lower = message.lower()
        selected_agents = []
        
        # Basic rule-based routing as fallback
        if any(word in message_lower for word in ["remember", "recall", "memory"]):
            selected_agents.append("memory_agent")
        
        if any(word in message_lower for word in ["task", "remind", "todo", "schedule"]):
            selected_agents.append("task_agent")
            
        if any(word in message_lower for word in ["sad", "happy", "angry", "feel", "emotion"]):
            selected_agents.append("emotion_agent")
            
        # Always include conversation agent as fallback
        selected_agents.append("conversation_agent")
        
        return selected_agents
    
    def update_agent_performance(self, agent_name: str, success: bool):
        """Update agent performance metrics"""
        if agent_name in self.agent_registry:
            self.agent_registry[agent_name]["usage_count"] += 1
            current_rate = self.agent_registry[agent_name]["success_rate"]
            new_rate = (current_rate * (self.agent_registry[agent_name]["usage_count"] - 1) + (1 if success else 0)) / self.agent_registry[agent_name]["usage_count"]
            self.agent_registry[agent_name]["success_rate"] = new_rate

# Global router instance
_router_instance = None

def get_router() -> IntelligentAgentRouter:
    """Get singleton router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = IntelligentAgentRouter()
        
        # Register default agents
        _router_instance.register_agent(
            "conversation_agent",
            "Handles general conversation and coordination",
            ["conversation", "coordination", "question_answering"],
            ["general chat", "coordination"],
            0.8
        )
        
        _router_instance.register_agent(
            "emotion_agent",
            "Analyzes emotional content and provides empathetic responses",
            ["emotion_detection", "sentiment_analysis", "empathy"],
            ["emotional support", "mood analysis"],
            0.7
        )
        
        _router_instance.register_agent(
            "memory_agent", 
            "Stores and retrieves user information",
            ["memory_storage", "information_retrieval", "personal_data"],
            ["personal information", "preferences", "user details"],
            0.9
        )
        
        _router_instance.register_agent(
            "task_agent",
            "Manages tasks and reminders",
            ["task_creation", "reminder_management", "scheduling"],
            ["productivity", "time management"],
            0.8
        )
        
    return _router_instance