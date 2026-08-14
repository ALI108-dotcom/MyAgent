"""MongoDB-backed Session Memory Manager with user data isolation & fallback."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.database import db_manager
from app.core.exceptions import APIException
from app.models.memory import ChatMessage, SessionMemory


class SessionMemoryManager:
    """Manages chat sessions and conversation history persistence with user isolation."""

    def __init__(self) -> None:
        self._in_memory_sessions: dict[str, SessionMemory] = {}

    async def create_session(
        self,
        title: str | None = None,
        initial_system_prompt: str | None = None,
        user_id: str | None = None,
    ) -> SessionMemory:
        """Create and store a new SessionMemory instance owned by user_id."""
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        session_title = title or f"Agent Session ({now[:10]})"

        initial_messages: list[ChatMessage] = []
        if initial_system_prompt:
            initial_messages.append(
                ChatMessage(
                    role="system",
                    content=initial_system_prompt,
                    timestamp=now,
                )
            )

        session = SessionMemory(
            session_id=session_id,
            user_id=user_id,
            title=session_title,
            messages=initial_messages,
            created_at=now,
            updated_at=now,
        )

        if db_manager.db is not None:
            try:
                doc = session.model_dump()
                await db_manager.db["sessions"].insert_one(doc)
            except Exception:
                self._in_memory_sessions[session_id] = session
        else:
            self._in_memory_sessions[session_id] = session

        return session

    async def get_session(
        self, session_id: str, requesting_user_id: str | None = None, is_admin: bool = False
    ) -> SessionMemory:
        """Retrieve session by session_id enforcing user ownership unless admin."""
        session: SessionMemory | None = None

        if db_manager.db is not None:
            try:
                doc = await db_manager.db["sessions"].find_one({"session_id": session_id})
                if doc:
                    doc.pop("_id", None)
                    session = SessionMemory(**doc)
            except Exception:
                pass

        if not session:
            session = self._in_memory_sessions.get(session_id)

        if not session:
            raise APIException(message=f"Session '{session_id}' not found.", status_code=404)

        if not is_admin and requesting_user_id and session.user_id:
            if session.user_id != requesting_user_id:
                raise APIException(
                    message="Access Denied: You do not own this session.", status_code=403
                )

        return session

    async def list_sessions(
        self, requesting_user_id: str | None = None, is_admin: bool = False
    ) -> list[SessionMemory]:
        """List sessions owned by requesting_user_id (or all sessions if admin)."""
        if db_manager.db is not None:
            try:
                query: dict[str, Any] = {}
                if not is_admin and requesting_user_id:
                    query["$or"] = [
                        {"user_id": requesting_user_id},
                        {"user_id": None},
                    ]
                cursor = db_manager.db["sessions"].find(query).sort("updated_at", -1)
                docs = await cursor.to_list(length=100)
                sessions = []
                for doc in docs:
                    doc.pop("_id", None)
                    sessions.append(SessionMemory(**doc))
                return sessions
            except Exception:
                pass

        filtered = []
        for s in self._in_memory_sessions.values():
            is_owner = s.user_id is None or s.user_id == requesting_user_id
            if is_admin or not requesting_user_id or is_owner:
                filtered.append(s)

        return sorted(filtered, key=lambda s: s.updated_at, reverse=True)

    async def add_message(
        self,
        session_id: str,
        message: ChatMessage,
        requesting_user_id: str | None = None,
        is_admin: bool = False,
    ) -> SessionMemory:
        """Append ChatMessage to specified session (creating if needed)."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            session = await self.get_session(
                session_id, requesting_user_id=requesting_user_id, is_admin=is_admin
            )
        except APIException:
            # Upsert new session memory if specified session_id does not exist yet
            session = SessionMemory(
                session_id=session_id,
                user_id=requesting_user_id,
                title=message.content[:30] if message.content else "Chat Session",
                messages=[],
                created_at=now,
                updated_at=now,
            )

        session.messages.append(message)
        session.updated_at = now

        if db_manager.db is not None:
            try:
                doc = session.model_dump()
                await db_manager.db["sessions"].replace_one(
                    {"session_id": session_id}, doc, upsert=True
                )
                return session
            except Exception:
                pass

        self._in_memory_sessions[session_id] = session
        return session

    async def delete_session(
        self, session_id: str, requesting_user_id: str | None = None, is_admin: bool = False
    ) -> bool:
        """Delete session after verifying user ownership."""
        session = await self.get_session(
            session_id, requesting_user_id=requesting_user_id, is_admin=is_admin
        )

        if db_manager.db is not None:
            try:
                res = await db_manager.db["sessions"].delete_one({"session_id": session_id})
                if res.deleted_count > 0:
                    return True
            except Exception:
                pass

        if session.session_id in self._in_memory_sessions:
            del self._in_memory_sessions[session.session_id]
            return True
        return False


session_manager = SessionMemoryManager()
