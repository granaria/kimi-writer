

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any

import utils
from MessageConverter import MessageConverter, logger
from ReconstructedMessage import ReconstructedMessage
from UserInputHandler import UserInputHandler
from ParametersONE import ParametersONE
from ads.projectManager import ProjectManager
from ads.systemPrompt import SystemPrompt
from utilsONE import UtilsONE

# Load environment variables from .env file
load_dotenv()


from tools.toolMap import ToolMap
from tools.compression import compress_context_impl
# from config import *

from ads.MoonshotClient import MoonshotClient
from ads.MessageBuilder import MessageBuilder
from ads.tokenizer import estimate_tokens
from ads.ContextCompressor import ContextCompressor
from ads.UserInput import UserInput



# ← Create ONE global instance (important!)
projectmanager = ProjectManager()
class AgentONE:
    def __init__(self):
        self.is_recovery:bool =  False
        self.user_prompt:str = ''
        self.moonshotclient = MoonshotClient()
        self.projectmanager = projectmanager
        self.toolmap = ToolMap()
        self.compressor = ContextCompressor(self.moonshotclient.client)
        self.tools = self.toolmap.get_tool_definitions()
        self.tool_map = self.toolmap.get_tool_map()
        # self.tool_map = get_tool_map(client=self.client.client, messages=self.messages, compressor=self.compressor)

        self.messages = [{"role": "system", "content": SystemPrompt.get_system_prompt()}]


    def append_prompt(self, user_prompt, is_recovery) -> None:
        # print(f"Input: {user_prompt}")
        # print(f"Recovery mode: {is_recovery}")

        self.user_prompt = user_prompt
        self.is_recovery = is_recovery
        self.messages.append({
            "role": "user",
            "content": f"[RECOVERED CONTEXT]\n{self.user_prompt}\n[END]" if self.is_recovery else self.user_prompt
        })

        self.start_print()

    def start_print(self):
        print("Recovery mode: Continuing from previous context\n") if self.is_recovery else None
        # print(f"\n📝 Task: {user_prompt}\n")

        print("=" * 60)
        print("Starting AgentONE")
        print("=" * 60)
        print(f"Model: {ParametersONE.MODEL}")
        print(f"Max iterations: {ParametersONE.MAX_ITERATIONS}")
        print(f"Context limit: {ParametersONE.TOKEN_LIMIT:,} tokens")
        print(f"Auto-compression at: {ParametersONE.COMPRESSION_THRESHOLD:,} tokens")
        print("=" * 60 + "\n")

    def backup_and_compress(self, iteration) -> None:

        """
                    print(f"\n💾 Auto-backup triggered (iteration {iteration})...")
                    try:
                        compression_result = compress_context_impl(
                            messages=agent.messages,
                            client=agent.moonshotclient.client,
                            model=ParametersONE.MODEL,
                            keep_recent=len(agent.messages)  # Keep all agent.messages, just save summary
                        )

                        backup_path = compression_result if isinstance(compression_result, (str, Path)) else compression_result.get("summary_file", "backup.json")

                        print(f"✓ Context auto-saved → {Path(backup_path).name}")
                        print("   (Can be recovered later with --recover flag)\n")

                        # if compression_result.get("summary_file"):
                            # print(f"✓ Backup saved: {os.path.basename(compression_result['summary_file'])}\n")
                    except Exception as e:
                        print(f"⚠️  Auto-backup failed: {e}")
                        print("   Continuing without backup...\n")

                    """

        # BACKUP_DIR = Path("backups")
        ParametersONE.BACKUP_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model_name = ParametersONE.MODEL.split("/")[-1]
        backup_filename = f"backup_iter{iteration:06d}_{timestamp}_{safe_model_name}.json"
        backup_path = ParametersONE.BACKUP_DIR / backup_filename
        tmp_path = backup_path.with_suffix(".tmp")  # Atomic write



        print(f"\n💾 Auto-backup triggered (iteration {iteration})...")
        try:
            # 1. Run context compression + summarization (the smart part)
            _result = compress_context_impl(
                messages=self.messages,
                client=self.moonshotclient.client,
                model=ParametersONE.MODEL,
                keep_recent=10,
                # extract_entities=True,  # Optional: better long-term recall
                # max_summary_tokens=1500,
            )

            # backup_path = _result if isinstance(_result, (str, Path)) else _result.get("summary_file", "backup.json")
            # Support both old (str/Path) and new (dict) return formats
            if isinstance(_result, (str, Path)):
                summary_file = Path(_result)
                metadata = {"summary_file": str(summary_file)}
            else:
                metadata = _result if isinstance(_result, dict) else {}
                summary_file = Path(metadata.get("summary_file", backup_path))

            print(f"✓ Context auto-saved → {Path(backup_path).name}")
            print("   (Can be recovered later with --recover flag)\n")
            # 2. Build rich backup metadata (critical for --recover and debugging)
            # ------------------------------------------------------------------
            backup_data = {
                "backup_version": 2,
                "timestamp": datetime.now().isoformat(),
                "iteration": iteration,
                "model": ParametersONE.MODEL,
                "total_messages": len(self.messages),
                "compressed_at": metadata.get("compressed_at"),
                "summary_tokens": metadata.get("summary_tokens"),
                "compression_ratio": round(
                    metadata.get("compression_ratio", 1.0), 3
                ),
                "kept_recent": 10,
                "summary_file": str(summary_file),
                "recovered_from": getattr(self, "recovered_from", None),
            }

            # 3. Atomic write: prevents half-written files on crash/OOM
            # ------------------------------------------------------------------
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            tmp_path.replace(backup_path)  # Atomic rename

            # 4. Cleanup: rotate old backups (keep last 5)
            # ------------------------------------------------------------------
            self._rotate_backups(ParametersONE.BACKUP_DIR, keep_last=5)

            print(f"✓ Context auto-saved → {backup_path.name}")
            print(f"   📁 Location: {backup_path.resolve()}")
            print(f"   ⚡ Ratio: ~{backup_data['compression_ratio']:.2f}x | "
                  f"Tokens saved: ~{metadata.get('tokens_saved', 'N/A')}\n")

            # logger.info("Auto-backup successful: %s (iter %d)", backup_path.name, iteration)


            # if compression_result.get("summary_file"):
            # print(f"✓ Backup saved: {os.path.basename(compression_result['summary_file'])}\n")
        except Exception as e:
            print(f"⚠️  Auto-backup failed: {e}")
            print("   Continuing without backup...\n")

    def _rotate_backups(self, backup_dir: Path, keep_last: int = 5) -> None:
        """Keep only the most recent N backup files to avoid filling disk."""
        try:
            backups = sorted(
                [p for p in backup_dir.glob("backup_iter*.json") if p.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            for old_backup in backups[keep_last:]:
                try:
                    old_backup.unlink()
                    logger.debug("Removed old backup: %s", old_backup.name)
                except OSError:
                    pass
        except Exception:
            pass  # Never crash the main loop over cleanup

    def check_and_compress(self) -> None:
        """
        Check token count and compress if needed.

        This is the core pre-API management step. Logs progress and updates self.messages.
        """
        """
                # Print a decorative header for each iteration to improve readability in logs/output
                # Uses f-string formatting with a centered title and Unicode box-drawing characters for aesthetics
                print(f"\n{' ITERATION {iteration} ':═^60}")

                # Section: Pre-API Token Management
                # This block estimates the current prompt size (in tokens) to avoid exceeding model limits
                # before sending to the LLM API, preventing errors or truncated responses

                # Try block to handle potential errors in token estimation (e.g., API downtime, invalid model)
                try:
                    # Call a utility function to estimate total tokens in the current agent.messages list
                    # Assumes UtilsONE is a custom module with OpenAI/Claude-compatible estimation logic
                    tokens = UtilsONE.estimate_token_count(agent.moonshotclient.base_url, agent.moonshotclient.api_key, ParametersONE.MODEL, agent.messages)

                    # Log the current token usage as a formatted string with commas for readability
                    # Includes percentage calculation for quick visual assessment of limit proximity
                    print(f"📊 Current tokens: {tokens:,}/{ParametersONE.TOKEN_LIMIT:,} ({tokens / ParametersONE.TOKEN_LIMIT * 100:.1f}%)")

                    # Conditional: Proactive Context Compression
                    # Triggers if the prompt is nearing the model's max token limit (e.g., 80-90% threshold)
                    # This helps maintain conversation history without hitting hard limits
                    if tokens >= ParametersONE.COMPRESSION_THRESHOLD:
                        # Alert the user/log that compression is being initiated
                        print(f"\n⚠️  Approaching token limit! Compressing context...")

                        # Invoke the compression function to prune/summarize old agent.messages
                        # Parameters:
                        # - agent.messages: The full conversation history (list of dicts with role/content)
                        # - client: API client instance (e.g., OpenAI) for potential summarization calls
                        # - model: The LLM model name for token-accurate handling
                        # - keep_recent: Number of recent exchanges to preserve verbatim (hardcoded to 10 here)
                        compression_result = compress_context_impl(
                            messages=agent.messages,
                            client=agent.moonshotclient.client,
                            model=ParametersONE.MODEL,
                            keep_recent=10
                        )
                        # Check if compression succeeded (result dict has the expected key)
                        if "compressed_messages" in compression_result:
                            # Update the global agent.messages list with the pruned version
                            agent.messages = compression_result["compressed_messages"]
                            # Log success message from the compression function
                            # print(f"✓ {compression_result['message']}")
                            # Log approximate tokens saved (fetched from result dict; fallback to 0 if missing)
                            # print(f"✓ Estimated tokens saved: ~{compression_result.get('tokens_saved', 0):,}")
                            # Re-estimate tokens post-compression to confirm the reduction
                            tokens = UtilsONE.estimate_token_count(agent.moonshotclient.base_url, agent.moonshotclient.api_key, ParametersONE.MODEL, agent.messages)

                            # Log the updated token count for verification
                            print(f"📊 New token count: {tokens:,}/{ParametersONE.TOKEN_LIMIT:,}\n")


                # Exception handler: Graceful fallback if token estimation fails
                # This prevents the entire loop from crashing due to transient issues
                except Exception as e:
                    # Log a warning with the error details, but don't halt execution
                    print(f"⚠️  Warning: Could not estimate token count: {e}")

                    # Set tokens to 0 as a safe default to skip compression logic
                    tokens = 0
                """
        try:
            tokens = UtilsONE.estimate_token_count(self.moonshotclient.base_url, self.moonshotclient.api_key, ParametersONE.MODEL, self.messages)
            print(
                f"📊 Current tokens: {tokens:,}/{ParametersONE.TOKEN_LIMIT:,} ({tokens / ParametersONE.TOKEN_LIMIT * 100:.1f}%)")

            if tokens >= ParametersONE.COMPRESSION_THRESHOLD:
                # print(f"\n⚠️  Approaching token limit! Compressing context...")
                compression_result = compress_context_impl(
                    messages=self.messages,
                    client=self.moonshotclient.client,
                    model=ParametersONE.MODEL,
                    keep_recent=10
                )

                if "compressed_messages" in compression_result:
                    self.messages = compression_result["compressed_messages"]

                    tokens = UtilsONE.estimate_token_count(self.moonshotclient.base_url, self.moonshotclient.api_key,
                                                           ParametersONE.MODEL, self.messages)


        except Exception as e:
            print(f"⚠️  Warning: Could not estimate token count: {e}")








    def run0(self):
        handler = UserInputHandler()
        user_prompt, is_recovery = handler.get_input()

        self.messages.append({
            "role": "user",
            "content": f"[RECOVERED CONTEXT]\n{user_prompt}\n[END]" if is_recovery else user_prompt
        })

        print("="*60)
        print("Starting AgentONE")
        print(f"Model: {ParametersONE.MODEL} | Max iterations: {ParametersONE.MAX_ITERATIONS}")
        print("="*60)

        for iteration in range(1, ParametersONE.MAX_ITERATIONS + 1):
            print(f"\n{' ITERATION {iteration} ':═^60}")

            # Token management
            tokens = estimate_tokens(self.messages)
            print(f"Tokens: {tokens:,}/{ParametersONE.TOKEN_LIMIT:,}")

            if tokens >= ParametersONE.COMPRESSION_THRESHOLD:
                print("Compressing context...")
                result = self.compressor.compress(self.messages)
                self.messages = result["compressed_messages"]

            if iteration % ParametersONE.BACKUP_INTERVAL == 0:
                self.compressor.backup(self.messages)

            # Call model
            stream = self.client.chat_completion(self.messages, self.tools)

            accumulated = MessageBuilder.from_stream()
            last_tool_idx = -1

            for chunk in stream:
                delta = chunk.choices[0].delta

                # Reasoning
                if getattr(delta, "reasoning_content", None):
                    print(delta.reasoning_content, end="", flush=True)
                    accumulated["reasoning_content"] += delta.reasoning_content

                # Content
                if delta.content:
                    print(delta.content, end="", flush=True)
                    accumulated["content"] += delta.content

                # Tool calls (streaming)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        while len(accumulated["tool_calls"]) <= idx:
                            accumulated["tool_calls"].append({"id": "", "function": {"name": "", "arguments": ""}, "type": "function"})

                        tool = accumulated["tool_calls"][idx]
                        if tc.id:
                            tool["id"] = tc.id
                        if tc.function.name:
                            tool["function"]["name"] = tc.function.name
                            if idx != last_tool_idx:
                                print(f"\nPreparing tool: {tc.function.name}")
                                last_tool_idx = idx
                        if tc.function.arguments:
                            tool["function"]["arguments"] += tc.function.arguments

            # Finalize assistant message
            assistant_msg = MessageBuilder.finalize(accumulated)
            self.messages.append(assistant_msg)

            if not accumulated["tool_calls"]:
                print("\n" + "="*60)
                print("TASK COMPLETED")
                print("="*60)
                break

            # Execute tools
            for tool_call in accumulated["tool_calls"]:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")

                print(f"\n→ Calling {name}({args})")

                func = self.tool_map.get(name)
                result = func(**args) if func else f"Error: Tool {name} not found"

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": str(result)
                })

        else:
            print("MAX ITERATIONS REACHED")
            self.compressor.backup(self.messages, "FINAL")