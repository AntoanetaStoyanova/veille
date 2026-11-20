from typing import Any
from unittest.mock import MagicMock


def make_llm(reply: dict[str, Any]) -> MagicMock:
    return MagicMock(return_value=reply)
