# Reconstruct the message object from accumulated data


from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
import json
import logging
from typing import Any, List, Dict
from pathlib import Path
from tools.compression import compress_context_impl
from ParametersONE import ParametersONE

logger = logging.getLogger(__name__)

class ReconstructedMessage:
    def __init__(self, role, content_text, reasoning_content, tool_calls_data):
        self.role = role
        self.content = content_text if content_text is not None else None
        self.reasoning_content = reasoning_content if reasoning_content is not None else None
        self.tool_calls = None

        if tool_calls_data:
            # Convert to proper format (mimicking OpenAI's ChatCompletionMessageToolCall)
            # Note: This uses dynamic class creation for simplicity; in production, use dataclasses or namedtuples
            self.tool_calls = []
            for tc in tool_calls_data:
                if tc.get("id"):  # Only add if we have an ID
                    function_obj = type('Function', (), {
                        'name': tc["function"]["name"],
                        'arguments': tc["function"]["arguments"]
                    })()

                    tool_call_obj = type('ToolCall', (), {
                        'id': tc["id"],
                        'type': 'function',
                        'function': function_obj
                    })()

                    self.tool_calls.append(tool_call_obj)



    def handle_tool_calls(self,
            agent,
            iteration: int,
    ) -> bool:
        """
        Process tool calls from the model response in a single, robust function.

        Returns:
            bool: True if task is completed (no tool calls), False if we should continue
        """
        '''
                   # Check if the model called any tools
                   if not rcmessage.tool_calls:
                       print("=" * 60)
                       print("✅ TASK COMPLETED")
                       print("=" * 60)
                       print(f"Completed in {iteration} iteration(s)")
                       print("=" * 60)
                       break



                   # Handle tool calls
                   print(f"🔧 Model decided to call {len(rcmessage.tool_calls)} tool(s):")





                   for tool_call in rcmessage.tool_calls:
                       func_name = tool_call.function.name
                       args_str = tool_call.function.arguments

                       try:
                           args = json.loads(args_str)
                       except json.JSONDecodeError:
                           args = {}

                       print(f"  → {func_name}")
                       print(f"    Arguments: {json.dumps(args, ensure_ascii=False, indent=6)}")

                       # Get the tool implementation
                       tool_func = agent.tool_map.get(func_name)

                       if not tool_func:
                           result = f"Error: Unknown tool '{func_name}'"
                           print(f"    ✗ {result}")
                       else:
                           # Special handling for compress_context (needs extra params)
                           if func_name == "compress_context":
                               result_data = compress_context_impl(
                                   messages=agent.messages,
                                   client=agent.moonshotclient.client,
                                   model=ParametersONE.MODEL,
                                   keep_recent=10
                               )
                               result = result_data.get("message", "Compression completed")

                               # Update agent.messages with compressed version
                               if "compressed_messages" in result_data:
                                   agent.messages = result_data["compressed_messages"]
                           else:
                               # Call the tool with its arguments
                               result = tool_func(**args)

                           # Print result (truncate if too long)
                           if len(str(result)) > 200:
                               print(f"    ✓ {str(result)[:200]}...")
                           else:
                               print(f"    ✓ {result}")

                       # Add tool result to agent.messages
                       tool_message = {
                           "role": "tool",
                           "tool_call_id": tool_call.id,
                           "name": func_name,
                           "content": str(result)
                       }
                       agent.messages.append(tool_message)
                       '''
        # No tool calls → task completed
        # if not getattr(rcmessage, "tool_calls", None):
        if not self.tool_calls:
            print("\n" + "=" * 70)
            print("TASK COMPLETED SUCCESSFULLY")
            print("=" * 70)
            print(f"   Completed in {iteration} iteration{'s' if iteration != 1 else ''}")
            print(f"   Model: {ParametersONE.MODEL}")
            print(f"   Final context length: {len(agent.messages)} messages")
            print("=" * 70)
            return True  # Done!



        # tool_calls = self.tool_calls
        print(f"\nModel requested {len(self.tool_calls)} tool call{'s' if len(self.tool_calls) > 1 else ''}")

        for idx, tool_call in enumerate(self.tool_calls, start=1):
            func_name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"

            print(f"\n  [{idx}/{len(self.tool_calls)}] Executing → {func_name}")

            # Parse arguments safely
            try:
                args = json.loads(raw_args)
                args_display = json.dumps(args, ensure_ascii=False, indent=2)
            except json.JSONDecodeError as e:
                args = {}
                args_display = f"<JSON parse error: {e}>\n{raw_args}"

            print(f"     Arguments:\n{args_display}")

            tool_func = agent.tool_map.get(func_name)
            if not tool_func:
                result: Any = "Error: Tool execution failed (unknown error)"
                print(f"    ✗ {result}")

            try:
                if func_name == "compress_context":
                    print("     Performing intelligent context compression...")
                    compression_result = compress_context_impl(
                        messages=agent.messages,
                        client=agent.moonshotclient.client,
                        model=ParametersONE.MODEL,
                        keep_recent=10,
                        # extract_entities=True,
                        # max_summary_tokens=2000
                    )

                    if compression_result.get("compressed_messages"):
                        _old_len = len(agent.messages)
                        agent.messages = compression_result["compressed_messages"]
                        saved = _old_len - len(agent.messages)
                        ratio = compression_result.get("compression_ratio", 1.0)
                        print(f"     Context compressed: {_old_len} → {len(agent.messages)} messages "
                              f"(-{saved}, ~{ratio:.2f}x)")

                    result = compression_result.get("message", "Compression completed")  # "Context compressed")

                elif tool_func:
                    result = tool_func(**args)
                    result_str = str(result)
                    if len(result_str) > 400:
                        result_str = result_str[:400] + "\n    ..."
                    print(f"     Success: {result_str}")
                else:
                    result = f"Error: Unknown tool '{func_name}'"
                    print(f"     Failed: Tool not found in agent.tool_map")

            except Exception as e:
                result = f"Tool crashed: {type(e).__name__}: {e}"
                print(f"     Failed: {result}")
                # logger.error(f"Tool '{func_name}' failed at iteration {iteration}", exc_info=True)

            # Append tool response (required by the API spec)
            agent.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": str(result)
            })

        print()  # Clean line break
        return False  # Continue loop
