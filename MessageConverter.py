# from __future__ import annotations

from typing import Any, Dict, List, Union, Optional
from dataclasses import dataclass
import json
import logging

# Optional: Use OpenAI types if available
try:
    from openai.types.chat import (
        ChatCompletionMessageParam,
        ChatCompletionToolMessageParam,
        ChatCompletionUserMessageParam,
        ChatCompletionAssistantMessageParam,
    )

    OPENAI_TYPES_AVAILABLE = True
except ImportError:
    OPENAI_TYPES_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MessageConverter:
    """
    A robust utility class to convert various message formats into OpenAI API-compatible dictionaries.

    Features:
    - Supports dict, OpenAI pydantic models, and custom objects
    - Preserves `reasoning_content` (for o1 models)
    - Handles multimodal content (text + images)
    - Safely serializes tool calls and tool responses
    - Extensible and type-safe
    """
    '''
    @staticmethod
    def convert_zero(msg: Any) -> Dict[str, Any]:
        """
        Converts a message object to a dictionary suitable for API calls.
        Preserves reasoning_content if present.

        Args:
            msg: Message object (can be OpenAI message object or dict)

        Returns:
            Dictionary representation of the message
        """
        if isinstance(msg, dict):
            return msg

        # Convert OpenAI message object to dict
        msg_dict = {
            "role": msg.role,
        }

        if msg.content:
            msg_dict["content"] = msg.content

        # Preserve reasoning_content if present
        if hasattr(msg, "reasoning_content"):
            reasoning = getattr(msg, "reasoning_content")
            if reasoning:
                msg_dict["reasoning_content"] = reasoning

        # Preserve tool calls if present
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]

        # Preserve tool call id for tool response messages
        if hasattr(msg, "tool_call_id") and msg.tool_call_id:
            msg_dict["tool_call_id"] = msg.tool_call_id

        if hasattr(msg, "name") and msg.name:
            msg_dict["name"] = msg.name

        return msg_dict
    '''
    @staticmethod
    def convert(msg: Any) -> Dict[str, Any]:
        """
        Convert a message object to an OpenAI API-compatible dictionary.

        Args:
            msg: Message object (dict, OpenAI model, or custom object)

        Returns:
            Dict[str, Any]: API-ready message dictionary

        Raises:
            ValueError: If the message is invalid or missing required fields
        """
        if msg is None:
            raise ValueError("Message cannot be None")

        # Pass through if already a dict
        if isinstance(msg, dict):
            return msg  # MessageConverter._validate_and_clean_dict(msg)

        # Handle OpenAI pydantic models (openai>=1.0.0)
        """
        if OPENAI_TYPES_AVAILABLE and isinstance(msg, (
                ChatCompletionMessageParam,
                ChatCompletionToolMessageParam,
                ChatCompletionUserMessageParam,
                ChatCompletionAssistantMessageParam,
        )):
            return msg.model_dump(exclude_none=True)
        """
        # Fallback: treat as generic object with attributes
        return MessageConverter._convert_from_object(msg)

    # ------------------------------------------------------------------ #
    # Internal conversion methods
    # ------------------------------------------------------------------ #

    @staticmethod
    def _convert_from_object(msg: Any) -> Dict[str, Any]:
        """Convert arbitrary object with attributes to API dict."""
        if not hasattr(msg, "role"):
            raise ValueError(f"Message object must have 'role' attribute: {type(msg)}")

        msg_dict: Dict[str, Any] = {"role": getattr(msg, "role")}

        # Content handling (text, list, or None)
        content = getattr(msg, "content", None)
        if content is not None:
            msg_dict["content"] = MessageConverter._normalize_content(content)

        # Preserve reasoning_content (o1-preview, o1-mini)
        if hasattr(msg, "reasoning_content"):
            reasoning = getattr(msg, "reasoning_content")
            if reasoning:
                msg_dict["reasoning_content"] = reasoning

        # Tool calls (assistant message)
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            msg_dict["tool_calls"] = [
                MessageConverter._serialize_tool_call(tc) for tc in msg.tool_calls
            ]

        # Tool response (tool message)
        if hasattr(msg, "tool_call_id") and getattr(msg, "tool_call_id", None):
            msg_dict["tool_call_id"] = msg.tool_call_id

        # Optional: name (for function/user messages)
        if hasattr(msg, "name") and getattr(msg, "name", None):
            msg_dict["name"] = msg.name

        return msg_dict

    @staticmethod
    def _normalize_content(content: Any) -> Any:
        """Normalize content to string or list of content parts."""
        if isinstance(content, (list, tuple)):
            return content  # Assume already in correct format
        elif isinstance(content, str):
            return content if content else None
        else:
            try:
                return str(content)
            except Exception as e:
                logger.warning(f"Failed to convert content to string: {e}")
                return None

    @staticmethod
    def _serialize_tool_call(tc: Any) -> Dict[str, Any]:
        """Serialize a single tool call."""
        if not hasattr(tc, "id") or not hasattr(tc, "function"):
            raise ValueError("Tool call must have 'id' and 'function'")

        function = tc.function
        if not hasattr(function, "name") or not hasattr(function, "arguments"):
            raise ValueError("Tool call function must have 'name' and 'arguments'")

        try:
            # Try to parse arguments as JSON if it's a string
            args = function.arguments
            if isinstance(args, str):
                args = json.loads(args)
        except (json.JSONDecodeError, AttributeError):
            args = args  # Leave as-is if not parsable

        return {
            "id": tc.id,
            "type": getattr(tc, "type", "function"),
            "function": {
                "name": function.name,
                "arguments": json.dumps(args) if isinstance(args, (dict, list)) else args
            }
        }

    @staticmethod
    def _validate_and_clean_dict(msg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean a raw dict before returning."""
        if "role" not in msg_dict:
            raise ValueError("Message dict must contain 'role'")

        cleaned = {"role": msg_dict["role"]}

        if "content" in msg_dict and msg_dict["content"] is not None:
            cleaned["content"] = MessageConverter._normalize_content(msg_dict["content"])

        for key in ["reasoning_content", "tool_calls", "tool_call_id", "name"]:
            if key in msg_dict and msg_dict[key] is not None:
                if key == "tool_calls" and msg_dict[key]:
                    cleaned[key] = [
                        MessageConverter._serialize_tool_call(tc) if not isinstance(tc, dict) else tc
                        for tc in msg_dict[key]
                    ]
                else:
                    cleaned[key] = msg_dict[key]

        return cleaned

    # ------------------------------------------------------------------ #
    # Convenience methods
    # ------------------------------------------------------------------ #

    @classmethod
    def convert_list(cls, messages: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert a list of messages.

        Args:
            messages: List of message objects

        Returns:
            List of API-compatible dicts
        """
        if not isinstance(messages, (list, tuple)):
            raise TypeError("Messages must be a list or tuple")

        return [cls.convert(msg) for msg in messages]