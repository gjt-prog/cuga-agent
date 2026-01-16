"""
CugaLite-Kaizen Integration

This module provides hooks to integrate Kaizen into CugaLite's execution flow:
1. Retrieve guidelines before task execution
2. Capture trajectory during execution
3. Save trajectory and generate tips after completion
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from cuga.backend.kaizen_integration.kaizen_adapter import KaizenAdapter
from cuga.backend.kaizen_integration.trajectory_capture import TrajectoryCapture
from cuga.backend.cuga_graph.state.agent_state import AgentState
from cuga.config import settings


class CugaLiteKaizenIntegration:
    """Integration layer between CugaLite and Kaizen."""
    
    def __init__(self):
        """Initialize the integration."""
        self.adapter: Optional[KaizenAdapter] = None
        self.trajectory: Optional[TrajectoryCapture] = None
        self.enabled = False
        
        # Initialize if Kaizen is enabled in settings
        if hasattr(settings, 'kaizen') and settings.kaizen.enabled:
            self._initialize()
    
    def _initialize(self):
        """Initialize Kaizen adapter and trajectory capture."""
        try:
            self.adapter = KaizenAdapter(
                kaizen_path=settings.kaizen.kaizen_path,
                namespace_id=settings.kaizen.namespace_id,
                provider=settings.kaizen.provider,
                enabled=settings.kaizen.enabled
            )
            
            self.trajectory = TrajectoryCapture()
            self.enabled = self.adapter.enabled
            
            if self.enabled:
                logger.info("✅ CugaLite-Kaizen integration initialized")
            else:
                logger.warning("⚠️  Kaizen integration failed to initialize")
                
        except Exception as e:
            logger.error(f"Failed to initialize Kaizen integration: {e}")
            self.enabled = False
    
    def get_guidelines_for_task(self, task: str, state: Optional[AgentState] = None) -> List[str]:
        """
        Retrieve relevant guidelines for a task.
        
        Args:
            task: Task description
            state: Optional agent state for context
            
        Returns:
            List of guideline strings
        """
        if not self.enabled or not self.adapter:
            return []
        
        if not settings.kaizen.retrieve_guidelines:
            return []
        
        try:
            limit = settings.kaizen.guideline_limit
            guidelines = self.adapter.get_guidelines(task, limit=limit)
            
            if guidelines and state:
                # Add guidelines to state metadata for visibility
                if not hasattr(state, 'kaizen_guidelines'):
                    state.kaizen_guidelines = []
                state.kaizen_guidelines = guidelines
            
            return guidelines
            
        except Exception as e:
            logger.error(f"Error retrieving guidelines: {e}")
            return []
    
    def format_guidelines_for_prompt(self, guidelines: List[str]) -> str:
        """
        Format guidelines for inclusion in the system prompt.
        
        Args:
            guidelines: List of guideline strings
            
        Returns:
            Formatted guidelines string
        """
        if not guidelines:
            return ""
        
        formatted = "\n\n## 📚 Relevant Guidelines from Past Executions\n\n"
        formatted += "The following guidelines were learned from previous successful task executions:\n\n"
        
        for i, guideline in enumerate(guidelines, 1):
            formatted += f"{i}. {guideline}\n"
        
        formatted += "\nConsider these guidelines when planning and executing this task.\n"
        
        return formatted
    
    def start_trajectory_capture(self, task: str, state: Optional[AgentState] = None):
        """
        Start capturing a new trajectory.
        
        Args:
            task: Initial task description
            state: Optional agent state
        """
        if not self.enabled or not self.trajectory:
            return
        
        try:
            self.trajectory.reset()
            self.trajectory.add_user_message(task)
            self.trajectory.set_metadata("task", task)
            self.trajectory.set_metadata("mode", "cuga_lite")
            
            if state:
                self.trajectory.set_metadata("thread_id", getattr(state, 'thread_id', None))
                self.trajectory.set_metadata("user_id", getattr(state, 'user_id', None))
            
            logger.debug("Started trajectory capture")
            
        except Exception as e:
            logger.error(f"Error starting trajectory capture: {e}")
    
    def capture_step(
        self,
        step_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Capture a step in the trajectory.
        
        Args:
            step_type: Type of step ('thought', 'code', 'tool_call', 'output', etc.)
            content: Step content
            metadata: Optional metadata
        """
        if not self.enabled or not self.trajectory:
            return
        
        try:
            step_metadata = {"step_type": step_type}
            if metadata:
                step_metadata.update(metadata)
            
            if step_type in ['thought', 'code', 'plan']:
                self.trajectory.add_assistant_message(content, step_metadata)
            elif step_type in ['output', 'result', 'error']:
                self.trajectory.add_system_message(content, step_metadata)
            else:
                self.trajectory.add_assistant_message(content, step_metadata)
            
        except Exception as e:
            logger.error(f"Error capturing step: {e}")
    
    def capture_code_execution(self, code: str, output: str, success: bool = True):
        """
        Capture a code execution step.
        
        Args:
            code: Executed code
            output: Execution output
            success: Whether execution was successful
        """
        if not self.enabled or not self.trajectory:
            return
        
        try:
            self.trajectory.add_code_execution(code, output, success)
        except Exception as e:
            logger.error(f"Error capturing code execution: {e}")
    
    def capture_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any):
        """
        Capture a tool call step.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            result: Tool execution result
        """
        if not self.enabled or not self.trajectory:
            return
        
        try:
            self.trajectory.add_tool_call(tool_name, args, result)
        except Exception as e:
            logger.error(f"Error capturing tool call: {e}")
    
    def save_trajectory(
        self,
        final_answer: Optional[str] = None,
        success: bool = True,
        state: Optional[AgentState] = None
    ) -> bool:
        """
        Save the captured trajectory to Kaizen.
        
        Args:
            final_answer: Optional final answer to add
            success: Whether the execution was successful
            state: Optional agent state
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.enabled or not self.adapter or not self.trajectory:
            return False
        
        if not settings.kaizen.save_trajectories:
            return False
        
        try:
            # Check minimum trajectory length
            min_length = settings.kaizen.min_trajectory_length
            if len(self.trajectory) < min_length:
                logger.debug(f"Trajectory too short ({len(self.trajectory)} < {min_length}), skipping save")
                return False
            
            # Add final answer if provided
            if final_answer:
                self.trajectory.add_assistant_message(
                    final_answer,
                    metadata={"type": "final_answer", "success": success}
                )
            
            # Set success metadata
            self.trajectory.set_metadata("success", success)
            
            # Get trajectory messages
            messages = self.trajectory.get_trajectory()
            
            # Generate task_id from state if available
            task_id = None
            if state:
                task_id = f"{getattr(state, 'thread_id', 'unknown')}_{getattr(state, 'user_id', 'unknown')}"
            
            # Save to Kaizen
            generate_tips = settings.kaizen.generate_tips and success
            saved = self.adapter.save_trajectory(
                messages=messages,
                task_id=task_id,
                generate_tips=generate_tips
            )
            
            if saved:
                logger.info(f"✅ Saved trajectory to Kaizen ({len(messages)} messages)")
            
            return saved
            
        except Exception as e:
            logger.error(f"Error saving trajectory: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get Kaizen integration statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.enabled or not self.adapter:
            return {"enabled": False}
        
        try:
            stats = self.adapter.get_stats()
            
            # Add trajectory info
            if self.trajectory:
                stats["current_trajectory_length"] = len(self.trajectory)
                stats["current_trajectory_metadata"] = self.trajectory.get_metadata()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global instance for easy access
_kaizen_integration: Optional[CugaLiteKaizenIntegration] = None


def get_kaizen_integration() -> CugaLiteKaizenIntegration:
    """
    Get or create the global Kaizen integration instance.
    
    Returns:
        CugaLiteKaizenIntegration instance
    """
    global _kaizen_integration
    
    if _kaizen_integration is None:
        _kaizen_integration = CugaLiteKaizenIntegration()
    
    return _kaizen_integration

# Made with Bob
