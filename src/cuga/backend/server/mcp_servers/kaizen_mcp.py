"""
Kaizen MCP Server

This MCP server exposes Kaizen's self-improving capabilities as tools that can be
integrated with CUGA Agent through the Model Context Protocol (MCP).

The server provides tools for:
1. Retrieving relevant guidelines for tasks
2. Saving execution trajectories
3. Adding manual guidelines
4. Getting knowledge base statistics
"""

import os
import sys
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger
from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Kaizen")

# Global Kaizen client instance
_kaizen_client = None
_kaizen_entity = None
_kaizen_exception = None


def _initialize_kaizen():
    """Initialize Kaizen client on first use."""
    global _kaizen_client, _kaizen_entity, _kaizen_exception

    if _kaizen_client is not None:
        return True

    try:
        # Get Kaizen path from environment or use default
        kaizen_path = os.environ.get('KAIZEN_PATH', os.path.expanduser('~/Dev/oss/kaizen'))
        kaizen_path = Path(kaizen_path)

        if not kaizen_path.exists():
            logger.error(f"Kaizen path does not exist: {kaizen_path}")
            return False

        # Add Kaizen to Python path
        kaizen_src = str(kaizen_path)
        if kaizen_src not in sys.path:
            sys.path.insert(0, kaizen_src)

        # Set provider from environment
        provider = os.environ.get('KAIZEN_PROVIDER', 'filesystem')
        os.environ['KAIZEN_PROVIDER'] = provider

        # Import Kaizen components
        from kaizen.frontend.client.kaizen_client import KaizenClient
        from kaizen.schema.core import Entity
        from kaizen.schema.exceptions import NamespaceNotFoundException

        # Store imports globally
        _kaizen_client = KaizenClient()
        _kaizen_entity = Entity
        _kaizen_exception = NamespaceNotFoundException

        logger.info(f"✅ Kaizen MCP server initialized (provider: {provider})")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Kaizen: {e}")
        return False


def _ensure_namespace(namespace_id: str) -> bool:
    """Ensure namespace exists, create if needed."""
    if not _kaizen_client:
        return False

    try:
        _kaizen_client.get_namespace_details(namespace_id)
        return True
    except _kaizen_exception:
        logger.info(f"Creating namespace: {namespace_id}")
        _kaizen_client.create_namespace(namespace_id)
        return True
    except Exception as e:
        logger.error(f"Error ensuring namespace: {e}")
        return False


def _normalize_message_content(content: Any) -> str:
    """Normalize message content to string format."""
    return str(content) if isinstance(content, list) else content


def _create_trajectory_entity(message: Dict[str, Any], task_id: str):
    """Create a trajectory entity from a message."""
    content = _normalize_message_content(message.get('content', ''))
    return _kaizen_entity(
        type='trajectory',
        content=content,
        metadata={
            "task_id": task_id,
            "role": message.get('role', 'unknown'),
            "message": message,
        },
    )


def _generate_and_save_tips(messages: List[Dict[str, Any]], namespace_id: str, task_id: str) -> int:
    """Generate tips from trajectory and save as guidelines. Returns count of tips generated."""
    try:
        from kaizen.llm.tips.tips import generate_tips as gen_tips

        tips = gen_tips(messages)
        if not tips:
            return 0

        logger.info(f"✨ Generated {len(tips)} tips from trajectory")

        tip_entities = [
            _kaizen_entity(
                type='guideline',
                content=tip,
                metadata={"source": "trajectory", "task_id": task_id},
            )
            for tip in tips
        ]

        _kaizen_client.update_entities(
            namespace_id=namespace_id, entities=tip_entities, enable_conflict_resolution=True
        )

        return len(tips)

    except Exception as e:
        logger.error(f"Error generating tips: {e}")
        return 0


@mcp.tool()
def get_guidelines(task: str, namespace_id: str = "cuga_lite", limit: int = 5) -> List[str]:
    """
    Retrieve relevant guidelines for a given task from Kaizen knowledge base.

    Args:
        task: Description of the task to get guidelines for
        namespace_id: Namespace ID to search in (default: "cuga_lite")
        limit: Maximum number of guidelines to retrieve (default: 5)

    Returns:
        List of guideline strings relevant to the task
    """
    if not _initialize_kaizen():
        return []

    try:
        _ensure_namespace(namespace_id)

        logger.info(f"🔍 Retrieving guidelines for task: {task[:100]}...")

        results = _kaizen_client.search_entities(
            namespace_id=namespace_id, query=task, filters={"type": "guideline"}, limit=limit
        )

        guidelines = [entity.content for entity in results]

        if guidelines:
            logger.info(f"✅ Retrieved {len(guidelines)} guidelines")
        else:
            logger.debug("No guidelines found")

        return guidelines

    except Exception as e:
        logger.error(f"Error retrieving guidelines: {e}")
        return []


@mcp.tool()
def save_trajectory(
    messages: List[Dict[str, Any]],
    namespace_id: str = "cuga_lite",
    task_id: Optional[str] = None,
    generate_tips: bool = True,
) -> Dict[str, Any]:
    """
    Save an execution trajectory to Kaizen and optionally generate tips.

    Args:
        messages: List of message dictionaries in OpenAI format (role, content)
        namespace_id: Namespace ID to save to (default: "cuga_lite")
        task_id: Optional task identifier for grouping related trajectories
        generate_tips: Whether to generate tips from the trajectory (default: True)

    Returns:
        Dictionary with success status and details
    """
    if not _initialize_kaizen():
        return {"success": False, "error": "Kaizen not initialized"}

    if not messages:
        return {"success": False, "error": "No messages provided"}

    try:
        _ensure_namespace(namespace_id)
        task_id = task_id or str(uuid.uuid4())

        logger.info(f"💾 Saving trajectory (task_id: {task_id}, messages: {len(messages)})")

        # Create and save trajectory entities
        entities = [_create_trajectory_entity(msg, task_id) for msg in messages]
        _kaizen_client.update_entities(
            namespace_id=namespace_id, entities=entities, enable_conflict_resolution=False
        )

        # Generate tips if requested
        tips_generated = _generate_and_save_tips(messages, namespace_id, task_id) if generate_tips else 0

        logger.info("✅ Trajectory saved successfully")

        return {
            "success": True,
            "task_id": task_id,
            "messages_saved": len(messages),
            "tips_generated": tips_generated,
        }

    except Exception as e:
        logger.error(f"Error saving trajectory: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_guideline(
    content: str, namespace_id: str = "cuga_lite", metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manually add a guideline to the Kaizen knowledge base.

    Args:
        content: Guideline content/text
        namespace_id: Namespace ID to add to (default: "cuga_lite")
        metadata: Optional metadata dictionary

    Returns:
        Dictionary with success status
    """
    if not _initialize_kaizen():
        return {"success": False, "error": "Kaizen not initialized"}

    try:
        _ensure_namespace(namespace_id)

        entity = _kaizen_entity(type='guideline', content=content, metadata=metadata or {})

        _kaizen_client.update_entities(
            namespace_id=namespace_id, entities=[entity], enable_conflict_resolution=True
        )

        logger.info(f"✅ Added guideline: {content[:100]}...")

        return {"success": True, "content": content}

    except Exception as e:
        logger.error(f"Error adding guideline: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_stats(namespace_id: str = "cuga_lite") -> Dict[str, Any]:
    """
    Get statistics about the Kaizen knowledge base.

    Args:
        namespace_id: Namespace ID to get stats for (default: "cuga_lite")

    Returns:
        Dictionary with knowledge base statistics
    """
    if not _initialize_kaizen():
        return {"enabled": False, "error": "Kaizen not initialized"}

    try:
        _ensure_namespace(namespace_id)

        namespace = _kaizen_client.get_namespace_details(namespace_id)

        # Count guidelines and trajectories
        guidelines = _kaizen_client.search_entities(
            namespace_id=namespace_id, filters={"type": "guideline"}, limit=1000
        )

        trajectories = _kaizen_client.search_entities(
            namespace_id=namespace_id, filters={"type": "trajectory"}, limit=1000
        )

        return {
            "enabled": True,
            "namespace_id": namespace_id,
            "provider": os.environ.get('KAIZEN_PROVIDER', 'filesystem'),
            "total_entities": namespace.num_entities,
            "guidelines_count": len(guidelines),
            "trajectories_count": len(trajectories),
            "created_at": str(namespace.created_at),
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"enabled": True, "error": str(e)}


if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport="stdio")

# Made with Bob
