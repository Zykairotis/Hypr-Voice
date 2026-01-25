"""
Agent Registry

Manages agent lifecycle - spawn, track, and destroy agents.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import uuid
import threading

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent status states."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    DESTROYED = "destroyed"


@dataclass
class AgentSession:
    """Represents an active agent session."""
    session_id: str
    agent_type: str
    status: AgentStatus
    query: str
    created_at: str
    updated_at: str
    parent_id: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "query": self.query,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "parent_id": self.parent_id,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class AgentRegistry:
    """
    Registry for managing agent sessions.
    
    Responsibilities:
    - Track all active agent sessions
    - Manage agent lifecycle (create, run, pause, complete, destroy)
    - Provide session lookup and filtering
    - Handle cleanup of stale sessions
    """
    
    def __init__(self, max_sessions: int = 100):
        self.max_sessions = max_sessions
        self._sessions: dict[str, AgentSession] = {}
        self._lock = threading.RLock()
        self._session_history: list[dict] = []  # Completed sessions for metrics
        
    def create_session(
        self,
        agent_type: str,
        query: str,
        session_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: dict = None,
    ) -> AgentSession:
        """
        Create a new agent session.
        
        Args:
            agent_type: Type of agent (e.g., "code-worker")
            query: Initial query for the agent
            session_id: Optional custom session ID
            parent_id: Optional parent session ID for subagents
            metadata: Optional metadata dictionary
            
        Returns:
            Created AgentSession
        """
        with self._lock:
            # Check capacity
            if len(self._sessions) >= self.max_sessions:
                self._cleanup_completed_sessions()
                
                if len(self._sessions) >= self.max_sessions:
                    raise RuntimeError(f"Maximum sessions ({self.max_sessions}) reached")
            
            session_id = session_id or str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            session = AgentSession(
                session_id=session_id,
                agent_type=agent_type,
                status=AgentStatus.CREATED,
                query=query,
                created_at=now,
                updated_at=now,
                parent_id=parent_id,
                metadata=metadata or {},
            )
            
            self._sessions[session_id] = session
            logger.info(f"Created session {session_id[:8]} for {agent_type}")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)
    
    def update_session(
        self,
        session_id: str,
        status: Optional[AgentStatus] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: dict = None,
    ) -> Optional[AgentSession]:
        """
        Update a session's state.
        
        Args:
            session_id: Session to update
            status: New status
            result: Result content
            error: Error message if any
            metadata: Additional metadata to merge
            
        Returns:
            Updated session or None if not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for update")
                return None
            
            if status:
                session.status = status
            if result is not None:
                session.result = result
            if error is not None:
                session.error = error
            if metadata:
                session.metadata.update(metadata)
            
            session.updated_at = datetime.utcnow().isoformat()
            
            return session
    
    def start_session(self, session_id: str) -> Optional[AgentSession]:
        """Mark a session as running."""
        return self.update_session(session_id, status=AgentStatus.RUNNING)
    
    def complete_session(self, session_id: str, result: str = None) -> Optional[AgentSession]:
        """Mark a session as completed."""
        return self.update_session(
            session_id, 
            status=AgentStatus.COMPLETED,
            result=result,
        )
    
    def error_session(self, session_id: str, error: str) -> Optional[AgentSession]:
        """Mark a session as errored."""
        return self.update_session(
            session_id,
            status=AgentStatus.ERROR,
            error=error,
        )
    
    def destroy_session(self, session_id: str) -> bool:
        """
        Destroy a session and clean up resources.
        
        Args:
            session_id: Session to destroy
            
        Returns:
            True if destroyed, False if not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            # Archive to history before removing
            self._session_history.append(session.to_dict())
            
            # Keep history bounded
            if len(self._session_history) > 1000:
                self._session_history = self._session_history[-500:]
            
            del self._sessions[session_id]
            logger.info(f"Destroyed session {session_id[:8]}")
            
            return True
    
    def list_sessions(
        self,
        status: Optional[AgentStatus] = None,
        agent_type: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> list[dict]:
        """
        List sessions with optional filtering.
        
        Args:
            status: Filter by status
            agent_type: Filter by agent type
            parent_id: Filter by parent session
            
        Returns:
            List of session dictionaries
        """
        with self._lock:
            sessions = list(self._sessions.values())
            
            if status:
                sessions = [s for s in sessions if s.status == status]
            if agent_type:
                sessions = [s for s in sessions if s.agent_type == agent_type]
            if parent_id:
                sessions = [s for s in sessions if s.parent_id == parent_id]
            
            return [s.to_dict() for s in sessions]
    
    def get_children(self, parent_id: str) -> list[AgentSession]:
        """Get all child sessions of a parent."""
        with self._lock:
            return [
                s for s in self._sessions.values()
                if s.parent_id == parent_id
            ]
    
    def get_active_count(self) -> int:
        """Get count of active (non-completed) sessions."""
        with self._lock:
            return sum(
                1 for s in self._sessions.values()
                if s.status in (AgentStatus.CREATED, AgentStatus.RUNNING, AgentStatus.PAUSED)
            )
    
    def _cleanup_completed_sessions(self):
        """Remove completed sessions to free space."""
        with self._lock:
            completed = [
                session_id for session_id, session in self._sessions.items()
                if session.status in (AgentStatus.COMPLETED, AgentStatus.ERROR, AgentStatus.DESTROYED)
            ]
            
            for session_id in completed:
                self.destroy_session(session_id)
            
            logger.info(f"Cleaned up {len(completed)} completed sessions")
    
    def get_stats(self) -> dict:
        """Get registry statistics."""
        with self._lock:
            status_counts = {}
            type_counts = {}
            
            for session in self._sessions.values():
                status_counts[session.status.value] = status_counts.get(session.status.value, 0) + 1
                type_counts[session.agent_type] = type_counts.get(session.agent_type, 0) + 1
            
            return {
                "total_sessions": len(self._sessions),
                "max_sessions": self.max_sessions,
                "active_count": self.get_active_count(),
                "by_status": status_counts,
                "by_type": type_counts,
                "history_count": len(self._session_history),
            }
    
    def get_sessions_by_type(self, agent_type: str, active_only: bool = True) -> list[AgentSession]:
        """
        Get all sessions of a specific agent type.
        
        Supports multiple instances of the same agent type running concurrently.
        
        Args:
            agent_type: Type of agent to filter
            active_only: If True, only return running/created sessions
            
        Returns:
            List of AgentSession objects
        """
        with self._lock:
            sessions = [
                s for s in self._sessions.values()
                if s.agent_type == agent_type
            ]
            
            if active_only:
                sessions = [
                    s for s in sessions
                    if s.status in (AgentStatus.CREATED, AgentStatus.RUNNING, AgentStatus.PAUSED)
                ]
            
            return sessions
    
    def spawn_child(
        self,
        parent_id: str,
        agent_type: str,
        query: str,
        metadata: dict = None,
    ) -> AgentSession:
        """
        Spawn a child sub-agent from a parent session.
        
        This allows the orchestrator to delegate tasks to specialized
        sub-agents and track the parent-child relationship.
        
        Args:
            parent_id: Parent session ID
            agent_type: Type of child agent to spawn
            query: Task/query for the child agent
            metadata: Optional metadata for the child
            
        Returns:
            Created child AgentSession
            
        Raises:
            ValueError: If parent session not found
        """
        with self._lock:
            parent = self._sessions.get(parent_id)
            if not parent:
                raise ValueError(f"Parent session {parent_id} not found")
            
            child_metadata = metadata or {}
            child_metadata["spawned_from"] = parent_id
            child_metadata["parent_agent_type"] = parent.agent_type
            
            child = self.create_session(
                agent_type=agent_type,
                query=query,
                parent_id=parent_id,
                metadata=child_metadata,
            )
            
            logger.info(f"Spawned child {child.session_id[:8]} ({agent_type}) from parent {parent_id[:8]}")
            
            return child
    
    def get_instance_count(self, agent_type: str) -> int:
        """
        Get count of active instances for an agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Number of active instances
        """
        return len(self.get_sessions_by_type(agent_type, active_only=True))
    
    def can_spawn_more(self, agent_type: str, max_per_type: int = 10) -> bool:
        """
        Check if more instances of an agent type can be spawned.
        
        Args:
            agent_type: Type of agent
            max_per_type: Maximum allowed instances per type
            
        Returns:
            True if more can be spawned
        """
        return self.get_instance_count(agent_type) < max_per_type
