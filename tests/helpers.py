from unittest.mock import MagicMock

import anthropic
from anthropic.types import Message, TextBlock, Usage


def make_client(reply: str) -> MagicMock:
    message = Message(
        id="msg_1",
        content=[TextBlock(type="text", text=reply)],
        model="test-model",
        role="assistant",
        stop_reason="end_turn",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=1, output_tokens=1),
    )
    client = MagicMock(spec=anthropic.Anthropic)
    client.messages.create.return_value = message
    return client
