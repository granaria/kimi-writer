from typing import List, Dict, Any

from ParametersONE import ParametersONE
from agentONE import AgentONE


class StreamingChat:

    def kimi_k2_streaming_chat(
            agent:AgentONE,
            iteration:int,
            # messages: List[Dict[str, Any]],
            # tools: List[Dict] = None,
            # model: str = ParametersONE.MODEL,
            # max_tokens: int = ParametersONE.MAX_TOKENS,
            # temperature: float = ParametersONE.TEMPERATURE,
    ) -> tuple[str, str, str, list | None]:

        # Call the model
        # try:
            print("🤖 Calling AgentONE-thinking model...\n")

            stream = agent.moonshotclient.client.chat.completions.create(
                model=ParametersONE.MODEL,
                messages=agent.messages,
                max_tokens=ParametersONE.MAX_TOKENS,  # 64K tokens
                tools=agent.tools,
                temperature=ParametersONE.TEMPERATURE,  # 1.0,
                stream=True,  # Enable streaming

                tool_choice="auto",
                # stream=True,

            )

            # Accumulate the streaming response
            reasoning_content = ""
            final_content = ""
            tool_calls = []
            # current_tool_calls = []  # in-progress
            role = None
            finish_reason = None

            # Track if we've printed headers
            reasoning_header = False
            response_header = False
            # tool_header = False
            last_tool_index = -1

            # Spinner for long argument generation
            spinner = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
            spinner_idx = 0
            print(f"\n🤖 调用 Kimi K2 模型... (第 {iteration} 次思考)\n")
            # Process the stream
            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason or finish_reason

                # Get role if present (first chunk)
                if hasattr(delta, "role") and delta.role:
                    role = delta.role

                # ==================== REASONING ====================
                # if getattr(delta, "reasoning_content", None):
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    if not reasoning_header:
                        print("=" * 60)
                        print(f"🧠 Reasoning (Iteration {iteration})")
                        print("=" * 60)
                        reasoning_header = True

                    print(delta.reasoning_content, end="", flush=True)
                    reasoning_content += delta.reasoning_content

                # ==================== FINAL CONTENT ====================

                # if delta.content:
                if hasattr(delta, "content") and delta.content:
                    # Close reasoning section if it was open
                    if reasoning_header and not response_header:
                        print("\n" + "=" * 60 + "\n")

                    if not response_header:
                        print("💬 Response:")
                        print("-" * 60)
                        response_header = True

                    print(delta.content, end="", flush=True)
                    final_content += delta.content

                # Handle tool_calls
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        # Initialize slot # Ensure we have enough slots in tool_calls
                        while len(tool_calls) <= idx:
                            tool_calls.append({
                                "id": None,
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                                "chars_received": 0
                            })

                        tc = tool_calls[idx]

                        # Print header when we start receiving a tool call
                        if idx != last_tool_index:
                            if reasoning_header or response_header:
                                print("\n" + "=" * 60 + "\n")

                            if hasattr(tc_delta, "function") and tc_delta.function.name:
                                print(f"🔧 Preparing tool call: {tc_delta.function.name}")
                                print("─" * 60)
                                tool_header = True
                                last_tool_index = idx

                        # ID
                        if tc_delta.id:
                            tc["id"] = tc_delta.id

                        # Arguments streaming
                        if hasattr(tc_delta, "function"):
                            if tc_delta.function.name:
                                tc["function"]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                args = tc_delta.function.arguments
                                tc["function"]["arguments"] += args
                                # tc["chars_received"] += len(args)
                                chars = len(tc["function"]["arguments"])

                                # Live progress (exactly like real Kimi)
                                words = chars // 5
                                spinner_char = spinner[spinner_idx % 8]
                                spinner_idx += 1
                                print(f"\r{spinner_char} 生成参数中... {chars:,} 字符 ≈ {words:,} 词", end="",
                                      flush=True)
                                '''
                                # Show progress indicator every 500 characters
                                if chars % 500 == 0 or chars < 100:
                                    # Calculate approximate words (rough estimate: 5 chars per word)
                                    words = tc["chars_received"] // 5
                                    print(f"\r💬 Generating arguments... {tc['chars_received']:,} characters (~{words:,} words)", end="", flush=True)
                                '''

            # =============== FINAL CLEANUP & SUMMARY ===============
            print()  # final newline after spinner
            '''
            # Print closing for content if it was printed
            if response_header:
                print("\n" + "-" * 60 + "\n")

            # Print completion for tool calls if any were received
            if tool_header:
                print("\n✓ Tool call complete")
                print("─" * 60 + "\n")
            '''

            # Tool call completion summary (Kimi style)
            if tool_calls and any(tc["function"]["name"] for tc in tool_calls):
                print("\n✓ 工具调用完成")
                for i, tc in enumerate(tool_calls):
                    if tc["function"]["name"]:
                        chars = len(tc["function"]["arguments"])
                        words = chars // 5
                        print(f"   {i + 1}. {tc['function']['name']} ({chars:,} 字符, ~{words:,} 词)")
                print("─" * 50 + "\n")

            # If final answer was empty (pure tool mode), show placeholder
            if not final_content.strip() and finish_reason != "tool_calls":
                print("（模型正在处理工具结果...）")
            """
            # Format final tool_calls exactly as OpenAI spec
            tool_calls_final = None
            if completed_tools:
                tool_calls_final = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    }
                    for tc in completed_tools
                ]
            """

            return (
                role,  # "assistant"
                final_content,  # Visible answer
                reasoning_content,  # Hidden o1-style reasoning
                # tool_calls_final,  # None or list of full tool calls
                tool_calls  # None or list of full tool calls
            )