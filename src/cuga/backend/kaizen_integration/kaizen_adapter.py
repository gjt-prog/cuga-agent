"""
Kaizen Adapter for CUGA Agent

This adapter provides a bridge between CUGA and Kaizen, enabling:
1. Retrieval of relevant guidelines before task execution
2. Saving trajectories after task completion
3. Automatic tip generation from successful executions
"""

import os
import sys
from typing import Optional, List, Dict, Any
from loguru import logger
from pathlib import Path


class KaizenAdapter:
    """Adapter for integrating Kaizen's self-improving capabilities into CUGA."""
    
    def __init__(
        self,
        kaizen_path: Optional[str] = None,
        namespace_id: str = "cuga_lite",
        provider: str = "filesystem",
        enabled: bool = True
    ):
        """
        Initialize the Kaizen adapter.
        
        Args:
            kaizen_path: Path to Kaizen installation (defaults to ~/Dev/oss/kaizen)
            namespace_id: Namespace ID for storing guidelines
            provider: Backend provider ('filesystem' or 'milvus')
            enabled: Whether Kaizen integration is enabled
        """
        self.enabled = enabled
        self.namespace_id = namespace_id
        self.provider = provider
        self.client = None
        
        if not self.enabled:
            logger.info("Kaizen integration is disabled")
            return
            
        # Set default kaizen path
        if kaizen_path is None:
            kaizen_path = os.path.expanduser("~/Dev/oss/kaizen")
        
        self.kaizen_path = Path(kaizen_path)
        
        # Initialize Kaizen client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Kaizen client by importing from the Kaizen installation."""
        try:
            # Add Kaizen to Python path
            kaizen_src = str(self.kaizen_path)
            if kaizen_src not in sys.path:
                sys.path.insert(0, kaizen_src)
            
            # Set environment variable for provider
            os.environ['KAIZEN_PROVIDER'] = self.provider
            
            # Import Kaizen client
            from kaizen.frontend.client.kaizen_client import KaizenClient
            from kaizen.schema.core import Entity
            from kaizen.schema.exceptions import NamespaceNotFoundException
            
            # Store imports for later use
            self.KaizenClient = KaizenClient
            self.Entity = Entity
            self.NamespaceNotFoundException = NamespaceNotFoundException
            
            # Create client instance
            self.client = KaizenClient()
            
            # Ensure namespace exists
            self._ensure_namespace()
            
            logger.info(f"✅ Kaizen adapter initialized successfully (namespace: {self.namespace_id}, provider: {self.provider})")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kaizen client: {e}")
            logger.warning("Kaizen integration will be disabled")
            self.enabled = False
            self.client = None
    
    def _ensure_namespace(self):
        """Ensure the namespace exists, create if it doesn't."""
        if not self.client:
            return
            
        try:
            self.client.get_namespace_details(self.namespace_id)
            logger.debug(f"Namespace '{self.namespace_id}' exists")
        except self.NamespaceNotFoundException:
            logger.info(f"Creating namespace '{self.namespace_id}'")
            self.client.create_namespace(self.namespace_id)
    
    def get_guidelines(self, task: str, limit: int = 5) -> List[str]:
        """
        Retrieve relevant guidelines for a given task.
        
        Args:
            task: Description of the task
            limit: Maximum number of guidelines to retrieve
            
        Returns:
            List of guideline strings
        """
        if not self.enabled or not self.client:
            return []
        
        try:
            logger.info(f"🔍 Retrieving guidelines for task: {task[:100]}...")
            
            results = self.client.search_entities(
                namespace_id=self.namespace_id,
                query=task,
                filters={"type": "guideline"},
                limit=limit
            )
            
            guidelines = [entity.content for entity in results]
            
            if guidelines:
                logger.info(f"✅ Retrieved {len(guidelines)} guidelines from Kaizen")
            else:
                logger.debug("No guidelines found for this task")
            
            return guidelines
            
        except Exception as e:
            logger.error(f"Error retrieving guidelines: {e}")
            return []
    
    def save_trajectory(
        self,
        messages: List[Dict[str, Any]],
        task_id: Optional[str] = None,
        generate_tips: bool = True
    ) -> bool:
        """
        Save a trajectory and optionally generate tips.
        
        Args:
            messages: List of message dictionaries (OpenAI format)
            task_id: Optional task identifier
            generate_tips: Whether to generate tips from the trajectory
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            import uuid
            task_id = task_id or str(uuid.uuid4())
            
            logger.info(f"💾 Saving trajectory (task_id: {task_id}, messages: {len(messages)})")
            
            # Save trajectory messages
            entities = []
            for message in messages:
                content = message.get('content', '')
                if isinstance(content, list):
                    # Handle multi-part content
                    content = str(content)
                
                entities.append(self.Entity(
                    type='trajectory',
                    content=content,
                    metadata={
                        "task_id": task_id,
                        "role": message.get('role', 'unknown'),
                        "message": message
                    }
                ))
            
            self.client.update_entities(
                namespace_id=self.namespace_id,
                entities=entities,
                enable_conflict_resolution=False
            )
            
            # Generate tips if requested
            if generate_tips:
                tips = self._generate_tips(messages)
                if tips:
                    logger.info(f"✨ Generated {len(tips)} tips from trajectory")
                    
                    # Save tips as guidelines
                    tip_entities = [
                        self.Entity(
                            type='guideline',
                            content=tip,
                            metadata={"source": "trajectory", "task_id": task_id}
                        )
                        for tip in tips
                    ]
                    
                    self.client.update_entities(
                        namespace_id=self.namespace_id,
                        entities=tip_entities,
                        enable_conflict_resolution=True
                    )
            
            logger.info("✅ Trajectory saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving trajectory: {e}")
            return False
    
    def _generate_tips(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        Generate tips from a trajectory using Kaizen's tip generation.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of generated tips
        """
        try:
            from kaizen.llm.tips.tips import generate_tips
            tips = generate_tips(messages)
            return tips
        except Exception as e:
            logger.error(f"Error generating tips: {e}")
            return []
    
    def add_guideline(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Manually add a guideline to the knowledge base.
        
        Args:
            content: Guideline content
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            entity = self.Entity(
                type='guideline',
                content=content,
                metadata=metadata or {}
            )
            
            self.client.update_entities(
                namespace_id=self.namespace_id,
                entities=[entity],
                enable_conflict_resolution=True
            )
            
            logger.info(f"✅ Added guideline: {content[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding guideline: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Kaizen knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        if not self.enabled or not self.client:
            return {"enabled": False}
        
        try:
            namespace = self.client.get_namespace_details(self.namespace_id)
            
            # Count guidelines and trajectories
            guidelines = self.client.search_entities(
                namespace_id=self.namespace_id,
                filters={"type": "guideline"},
                limit=1000
            )
            
            trajectories = self.client.search_entities(
                namespace_id=self.namespace_id,
                filters={"type": "trajectory"},
                limit=1000
            )
            
            return {
                "enabled": True,
                "namespace_id": self.namespace_id,
                "provider": self.provider,
                "total_entities": namespace.num_entities,
                "guidelines_count": len(guidelines),
                "trajectories_count": len(trajectories),
                "created_at": str(namespace.created_at)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"enabled": True, "error": str(e)}

# Made with Bob
