#!/usr/bin/env python3
"""
AgentONE Writing Agent - An autonomous agent for creative writing tasks.

This agent uses the AgentONE-thinking model to create novels, books,
and short story collections based on user prompts.
"""

import os
import signal
import sys
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv


from MessageConverter import MessageConverter
from ReconstructedMessage import ReconstructedMessage

from ParametersONE import ParametersONE
from UserInputHandler import UserInputHandler
from ads.streamingChat import StreamingChat
from agentONE import AgentONE
from utilsONE import UtilsONE
from ads.systemPrompt import SystemPrompt
# Load environment variables from .env file
load_dotenv()

from tools.compression import compress_context_impl

# write a short story with the style of murakami in 1Q84

signal.signal(signal.SIGINT, UtilsONE.graceful_shutdown)  # Ctrl+C
signal.signal(signal.SIGTERM, UtilsONE.graceful_shutdown)  # Docker stop / k8s kill

def main():

    agent = AgentONE()

    handler = UserInputHandler()
    user_prompt, is_recovery = handler.get_input()
    agent.append_prompt(user_prompt, is_recovery)


    # Main agent loop - outer loop for multiple iterations of the conversation or task
    # This simulates a long-running agent or chat session where context builds up over time
    for iteration in range(1, ParametersONE.MAX_ITERATIONS + 1):
        agent.check_and_compress()
        # --------------------------------------------------------------------------------------------------------------
        # Auto-backup every N iterations
        if iteration % ParametersONE.BACKUP_INTERVAL == 0:
            agent.backup_and_compress(iteration)

        # Call the model
        try:

            role, final_content, reasoning_content, tool_calls = StreamingChat.kimi_k2_streaming_chat(agent, iteration)

            # Reconstruct the message object from accumulated data
            rcmessage = ReconstructedMessage(role or "assistant", final_content, reasoning_content, tool_calls)
            # Convert message to dict and add to history
            # Important: preserve the full message object structure
            agent.messages.append(MessageConverter.convert(rcmessage))


            rcmessage.handle_tool_calls(agent, iteration)



        except KeyboardInterrupt:
            UtilsONE.graceful_shutdown(agent)
        
        except Exception as e:
            print(f"\n✗ Error during iteration {iteration}: {e}")
            print(f"Attempting to continue...\n")
            continue
    
    # If we hit max iterations
    if iteration >= ParametersONE.MAX_ITERATIONS:
        print("\n" + "=" * 60)
        print("⚠️  MAX ITERATIONS REACHED")
        print("=" * 60)
        print(f"\nReached maximum of {ParametersONE.MAX_ITERATIONS} iterations.")
        print("Saving final context...")
        
        try:
            compression_result = compress_context_impl(
                messages=agent.messages,
                client=agent.moonshotclient.client,
                model=ParametersONE.MODEL,
                keep_recent=len(agent.messages)
            )
            if compression_result.get("summary_file"):
                print(f"✓ Context saved to: {compression_result['summary_file']}")
                print(f"\nTo resume, run:")
                print(f"  python AgentONE writer.py --recover {compression_result['summary_file']}")
        except Exception as e:
            print(f"✗ Error saving context: {e}")


if __name__ == "__main__":
    main()

