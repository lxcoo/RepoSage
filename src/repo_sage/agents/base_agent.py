"""Base agent class with common functionality."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from rich.console import Console

from repo_sage.llm.provider import LLMProvider


@dataclass
class AgentTask:
    """Represents a task assigned to an agent."""
    task_id: str
    task_type: str
    input_data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class AgentMessage:
    """Message passed between agents."""
    sender: str
    receiver: str
    message_type: str  # request, response, notify
    payload: Dict[str, Any]


class BaseAgent(ABC):
    """Base class for all RepoSage agents."""
    
    def __init__(self, name: str, llm_provider: LLMProvider, console: Optional[Console] = None):
        self.name = name
        self.llm = llm_provider
        self.console = console or Console()
        self.message_queue: List[AgentMessage] = []
        self.task_history: List[AgentTask] = []
    
    def log(self, message: str, style: str = "blue"):
        """Log a message with agent identification."""
        self.console.print(f"[{style}][{self.name}][/{style}] {message}")
    
    def send_message(self, receiver: str, message_type: str, payload: Dict[str, Any]) -> AgentMessage:
        """Send a message to another agent."""
        msg = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            payload=payload
        )
        self.message_queue.append(msg)
        return msg
    
    def receive_messages(self) -> List[AgentMessage]:
        """Retrieve messages addressed to this agent."""
        my_messages = [m for m in self.message_queue if m.receiver == self.name]
        self.message_queue = [m for m in self.message_queue if m.receiver != self.name]
        return my_messages
    
    def execute_task(self, task: AgentTask) -> AgentTask:
        """Execute a task and update its status."""
        self.log(f"Starting task: {task.task_id}")
        task.status = "running"
        
        try:
            result = self._process_task(task)
            task.result = result
            task.status = "completed"
            self.log(f"Task completed: {task.task_id}", style="green")
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            self.log(f"Task failed: {task.task_id} - {e}", style="red")
        
        self.task_history.append(task)
        return task
    
    @abstractmethod
    def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Override this method to implement agent-specific logic."""
        pass
    
    def _llm_json_completion(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Get a JSON response from the LLM."""
        response = self.llm.complete(system_prompt, user_prompt)
        
        # Try to extract JSON from markdown code blocks
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: return raw response wrapped
            return {"raw_response": response, "parse_error": True}
