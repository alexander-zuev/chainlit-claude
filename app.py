import chainlit as cl
from anthropic_service.claude_assistant import ClaudeAssistant
from dotenv import load_dotenv

load_dotenv()

anthropic_service = None


@cl.on_chat_start
async def start():
    global anthropic_service
    anthropic_service = ClaudeAssistant()

    welcome_message = (
        "👋 Welcome to the Claude 3.5 Sonnet with prompt caching enabled.\n"
        "📖 After each message, prompt caching stats are sent.\n"
        "💬 Try having a long conversation and see how prompt caching saves time & costs!"
    )
    await cl.Message(content=welcome_message).send()


@cl.on_message
async def main(message: cl.Message):
    global anthropic_service

    try:
        response_message = cl.Message(content="")
        async for item in anthropic_service.generate_response(message.content):
            if item["type"] == "chunk":
                await response_message.stream_token(item["content"])
            elif item["type"] == "tool_use":
                # Create a step for tool use
                with cl.Step(name=f"Using tool: {item['name']}") as step:
                    step.input = item['input']
                    step.output = f"URLs parsed: {item['result']['urls_parsed']}"
                    await step.send()
            elif item["type"] == "final":
                await response_message.send()

                metrics = item["metrics"]
                metrics_message = (
                    "📊 *Performance Metrics*:\n"
                    f"⏱️  - Time taken: {metrics['time_taken']:.2f} seconds\n"
                    f"📥  - User input tokens: {metrics['input_tokens']}\n"
                    f"📤  - Output tokens: {metrics['output_tokens']}\n"
                    f"💾  - Input tokens (cache read): {metrics['input_tokens_cache_read']}\n"
                    f"🆕  - Input tokens (cache create): {metrics['input_tokens_cache_create']}\n"
                    f"📈  - {metrics['percentage_cached']:.1f}% of input prompt cached ({metrics['total_input_tokens']} tokens)"
                )
                await cl.Message(content=metrics_message).send()

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        await cl.Message(content=error_message).send()