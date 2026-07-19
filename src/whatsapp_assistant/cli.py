"""Interactive CLI for local testing, without going through WhatsApp/Meta.

Ported from dls-chatbot's interfaces/cli.py, adapted to:
- the ChatService/ChatMessage abstraction (no ADK types here);
- a single continuous session per user (no separate "create session" step —
  ChatService resolves session_id from user_id automatically);
- an explicit "/reset" command wired to ChatService.reset_session().
"""

import asyncio
import time
from argparse import ArgumentParser, Namespace

from dotenv import load_dotenv

from whatsapp_assistant.config import get_settings
from whatsapp_assistant.services.adk_chat_service import ADKChatService, build_runner
from whatsapp_assistant.services.chat_service import ChatMessage, ChatService

RESET_COMMANDS = {"/reset"}
EXIT_COMMANDS = {"exit", "quit", "q"}


async def chat_loop(chat_service: ChatService, user_id: str, stream: bool) -> None:
    print(f"User: {user_id}  [mode: {'streaming' if stream else 'non-streaming'}]")
    print(f"Type {', '.join(EXIT_COMMANDS)} to quit, /reset to clear the history.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError, KeyboardInterrupt:
            print("\nGoodbye!")
            break

        if user_input.lower() in EXIT_COMMANDS:
            print("Goodbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in RESET_COMMANDS:
            await chat_service.reset_session(user_id)
            print("(history cleared)\n")
            continue

        message = ChatMessage(user_id=user_id, text=user_input)

        if stream:
            printed_header = False
            async for chunk in chat_service.send_stream_async(message):
                if not printed_header:
                    print("\nAgent: ", end="", flush=True)
                    printed_header = True
                for word in chunk.split():
                    for letter in word:
                        print(letter, end="", flush=True)
                        time.sleep(0.002)  # simulated typing effect
                    print(" ", end="", flush=True)
            if printed_header:
                print("\n")
        else:
            response = await chat_service.send_async(message)
            print(f"\nAgent: {response}\n")


def add_arguments(parser: ArgumentParser) -> None:
    """Register CLI-specific arguments onto *parser* (a parser or subparser)."""
    parser.add_argument(
        "--user-id",
        default="dev-user",
        help="Identifier used for the session (default: 'dev-user')",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming and wait for the full response before printing",
    )


def run(args: Namespace) -> None:
    """Start the CLI using an already-parsed args namespace."""
    load_dotenv()
    settings = get_settings()
    chat_service = ADKChatService(build_runner(settings))
    asyncio.run(
        chat_loop(chat_service, user_id=args.user_id, stream=not args.no_stream)
    )


def run_cli() -> None:
    """Standalone entry point (`whatsapp-assistant-cli`) — parses sys.argv on its own."""
    parser = ArgumentParser(description="WhatsApp Assistant — interactive dev CLI")
    add_arguments(parser)
    run(parser.parse_args())


if __name__ == "__main__":
    run_cli()
