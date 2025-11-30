import sys
from pathlib import Path
from typing import List, Dict, Any
import httpx
import logging
import json

import agentONE
from ParametersONE import ParametersONE
from tools.compression import compress_context_impl

class UtilsONE:

    logger = logging.getLogger(__name__)

    @staticmethod
    def estimate_token_count(base_url: str, api_key: str, model: str, messages: List[Dict]) -> int:
        """
        Estimate the token count for the given messages using the Moonshot API.

        Note: Token estimation uses api.moonshot.ai (not .cn)

        Args:
            base_url: The base URL for the API (will be converted to .ai for token endpoint)
            api_key: The API key for authentication
            model: The model name
            messages: List of message dictionaries

        Returns:
            Total token count
        """
        # Convert messages to serializable format (remove non-serializable objects)
        serializable_messages: list = []
        for msg in messages:
            if hasattr(msg, 'model_dump'):
                # OpenAI SDK message object
                msg_dict = msg.model_dump()
            elif isinstance(msg, dict):
                msg_dict = msg.copy()
            else:
                msg_dict = {"role": "assistant", "content": str(msg)}

            # Clean up the message to only include serializable fields
            clean_msg = {}
            if 'role' in msg_dict:
                clean_msg['role'] = msg_dict['role']
            if 'content' in msg_dict and msg_dict['content']:
                clean_msg['content'] = msg_dict['content']
            if 'name' in msg_dict:
                clean_msg['name'] = msg_dict['name']
            if 'tool_calls' in msg_dict and msg_dict['tool_calls']:
                clean_msg['tool_calls'] = msg_dict['tool_calls']
            if 'tool_call_id' in msg_dict:
                clean_msg['tool_call_id'] = msg_dict['tool_call_id']

            serializable_messages.append(clean_msg)

        # Both token estimation and chat use api.moonshot.ai
        token_base_url = base_url

        # Make the API call
        with httpx.Client(
                base_url=token_base_url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0
        ) as client:
            response = client.post(
                "/tokenizers/estimate-token-count",
                json={
                    "model": model,
                    "messages": serializable_messages
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("total_tokens", 0)

    import sys
    import signal
    from pathlib import Path
    from datetime import datetime

    # ─────────────────────────────────────────────────────────────────────────────
    # Graceful shutdown on Ctrl+C – saves context reliably, never loses work
    # ─────────────────────────────────────────────────────────────────────────────
    @staticmethod
    def graceful_shutdown(agent, signum=None, frame=None):
        print("\n\nUser requested shutdown – performing emergency context save...")

        try:
            print("   Running final context compression (keeping everything)...", end=" ")

            # Force‑keep ALL recent messages – we don’t want any summarization on exit
            result = compress_context_impl(
                messages=agent.messages,
                client=agent.moonshotclient.client,
                model=ParametersONE.MODEL,
                keep_recent=len(agent.messages),  # <-- keep 100% of history
                # extract_entities=True,
                # max_summary_tokens=4000,  # generous limit for final save
                # force_save=True  # bypass any size thresholds
            )

            # Unified path extraction (supports str/Path or dict return)
            if isinstance(result, (str, Path)):
                final_path = Path(result)
            else:
                final_path = Path(result.get("summary_file") or "emergency_backup.json")

            # Pretty success message
            print(f"SUCCESS")
            print(f"   Full context saved → {final_path.name}")
            print(f"   Location: {final_path.resolve()}")
            print(f"   Size: {final_path.stat().st_size // 1024:,} KB")
            print(f"\n   To resume later, run:")
            print(f"   python AgentONE-writer.py --recover \"{final_path}\"")

            # Optional: copy to a timestamped "latest" symlink for ultra‑fast resume
            latest_link = Path("backups/LATEST_RECOVERY.json")
            latest_link.parent.mkdir(parents=True, exist_ok=True)
            try:
                latest_link.unlink(missing_ok=True)
                latest_link.symlink_to(final_path)
                print(f"   Quick‑resume link updated → {latest_link}")
            except Exception:
                pass  # symlinks not supported on Windows sometimes

        except Exception as e:
            print(f"FAILED (context may be lost)")
            print(f"   Error during emergency save: {e}")
            # Last‑ditch raw dump
            try:
                _raw_path = Path("backups/EMERGENCY_RAW_DUMP.json")
                _raw_path.parent.mkdir(parents=True, exist_ok=True)
                _raw_path.write_text(
                    json.dumps(agent.messages, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"   Raw message dump saved → {_raw_path}")
            except Exception:
                pass

        finally:
            print("\nGoodbye!\n")
            sys.exit(0)
'''
    # ─────────────────────────────────────────────────────────────────────────────
    # Register the handler – works for both Ctrl+C and SIGTERM (Docker/k8s)
    # ─────────────────────────────────────────────────────────────────────────────
    signal.signal(signal.SIGINT, graceful_shutdown)  # Ctrl+C
    signal.signal(signal.SIGTERM, graceful_shutdown)  # Docker stop / k8s kill

    # Also keep the classic except block as a safety net
    try:
        # ← your main loop here →
        ...
    except KeyboardInterrupt:
        # This will now instantly trigger the function above
        _graceful_shutdown()
'''