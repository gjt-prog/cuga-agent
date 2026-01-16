"""
Trajectory Capture for CUGA-Kaizen Integration

This module captures execution trajectories from CUGA's lite mode
and formats them for Kaizen's learning system.
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage


class TrajectoryCapture:
    """Captures and formats execution trajectories for Kaizen."""
    
    def __init__(self):
        """Initialize the trajectory capture."""
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def reset(self):
        """Reset the captured trajectory."""
        self.messages = []
        self.metadata = {}
    
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a user message to the trajectory.
        
        Args:
            content: Message content
            metadata: Optional metadata
        """
        message = {
            "role": "user",
            "content": content
        }
        if metadata:
            message["metadata"] = metadata
        
        self.messages.append(message)
        logger.debug(f"Added user message to trajectory (total: {len(self.messages)})")
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add an assistant message to the trajectory.
        
        Args:
            content: Message content
            metadata: Optional metadata
        """
        message = {
            "role": "assistant",
            "content": content
        }
        if metadata:
            message["metadata"] = metadata
        
        self.messages.append(message)
        logger.debug(f"Added assistant message to trajectory (total: {len(self.messages)})")
    
    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a system message to the trajectory.
        
        Args:
            content: Message content
            metadata: Optional metadata
        """
        message = {
            "role": "system",
            "content": content
        }
        if metadata:
            message["metadata"] = metadata
        
        self.messages.append(message)
        logger.debug(f"Added system message to trajectory (total: {len(self.messages)})")
    
    def add_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any):
        """
        Add a tool call to the trajectory.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            result: Tool execution result
        """
        # Add tool call as assistant message
        tool_call_content = f"Tool: {tool_name}\nArguments: {args}"
        self.add_assistant_message(
            tool_call_content,
            metadata={"type": "tool_call", "tool": tool_name, "args": args}
        )
        
        # Add tool result as system message
        result_content = f"Tool Result: {str(result)[:500]}"  # Limit result length
        self.add_system_message(
            result_content,
            metadata={"type": "tool_result", "tool": tool_name}
        )
    
    def add_code_execution(self, code: str, output: str, success: bool = True):
        """
        Add a code execution to the trajectory.
        
        Args:
            code: Executed code
            output: Execution output
            success: Whether execution was successful
        """
        # Add code as assistant message
        self.add_assistant_message(
            f"```python\n{code}\n```",
            metadata={"type": "code_execution", "success": success}
        )
        
        # Add output as system message
        self.add_system_message(
            f"Execution Output:\n{output[:1000]}",  # Limit output length
            metadata={"type": "execution_output", "success": success}
        )
    
    def add_langchain_messages(self, messages: List[BaseMessage]):
        """
        Add LangChain messages to the trajectory.
        
        Args:
            messages: List of LangChain BaseMessage objects
        """
        for msg in messages:
            if isinstance(msg, HumanMessage):
                self.add_user_message(msg.content)
            elif isinstance(msg, AIMessage):
                self.add_assistant_message(msg.content)
            else:
                # Handle other message types as system messages
                self.add_system_message(str(msg.content))
    
    def set_metadata(self, key: str, value: Any):
        """
        Set trajectory metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_trajectory(self) -> List[Dict[str, Any]]:
        """
        Get the captured trajectory.
        
        Returns:
            List of message dictionaries
        """
        return self.messages.copy()
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get the trajectory metadata.
        
        Returns:
            Metadata dictionary
        """
        return self.metadata.copy()
    
    def to_openai_format(self) -> List[Dict[str, str]]:
        """
        Convert trajectory to OpenAI message format.
        
        Returns:
            List of messages in OpenAI format
        """
        openai_messages = []
        for msg in self.messages:
            openai_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def summarize(self) -> str:
        """
        Create a summary of the trajectory.
        
        Returns:
            Summary string
        """
        user_msgs = sum(1 for m in self.messages if m["role"] == "user")
        assistant_msgs = sum(1 for m in self.messages if m["role"] == "assistant")
        system_msgs = sum(1 for m in self.messages if m["role"] == "system")
        
        tool_calls = sum(
            1 for m in self.messages 
            if m.get("metadata", {}).get("type") == "tool_call"
        )
        
        code_execs = sum(
            1 for m in self.messages 
            if m.get("metadata", {}).get("type") == "code_execution"
        )
        
        summary = f"""Trajectory Summary:
- Total messages: {len(self.messages)}
- User messages: {user_msgs}
- Assistant messages: {assistant_msgs}
- System messages: {system_msgs}
- Tool calls: {tool_calls}
- Code executions: {code_execs}
- Metadata: {self.metadata}
"""
        return summary
    
    def __len__(self) -> int:
        """Return the number of messages in the trajectory."""
        return len(self.messages)
    
    def __repr__(self) -> str:
        """Return a string representation of the trajectory."""
        return f"TrajectoryCapture(messages={len(self.messages)}, metadata={self.metadata})"

# Made with Bob
