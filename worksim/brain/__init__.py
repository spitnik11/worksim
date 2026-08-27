"""AgentBrain — the swappable seam that powers every persona and the evaluator.

This is THE most important interface in WorkSim. Today one implementation calls a
cloud LLM (`brain/llm.py`). The stated end goal is to train our own model on the
`(context -> work -> grade -> reward)` data the sim produces and drop it in behind this
same interface — so keep `complete()` minimal and provider-agnostic.

`get_brain()` is the factory/registry; the future trained-model brain registers here.
`FakeBrain` is deterministic and offline, so the whole pipeline is testable without a key.
"""

import os
from abc import ABC, abstractmethod
from typing import Callable, Optional

# A chat message: {"role": "user"|"assistant", "content": <str>}.
Message = dict


class AgentBrain(ABC):
    """Turn a system prompt + message history into text. That's the whole contract."""

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[Message],
        *,
        max_tokens: int = 8000,
        effort: str = "medium",
    ) -> str:
        ...


class FakeBrain(AgentBrain):
    """Deterministic brain for tests and offline runs.

    - `canned`: a list of replies returned in order (raises if exhausted).
    - `responder`: a callable (system, messages) -> str for custom behavior.
    - default: echoes a stable stub referencing the last user message, so pipeline
      wiring can be exercised without a network or key.
    """

    def __init__(
        self,
        canned: Optional[list[str]] = None,
        responder: Optional[Callable[[str, list[Message]], str]] = None,
    ):
        self._canned = list(canned) if canned else None
        self._responder = responder
        self.calls: list[dict] = []  # inspectable in tests

    def complete(self, system, messages, *, max_tokens=8000, effort="medium") -> str:
        self.calls.append({"system": system, "messages": messages, "effort": effort})
        if self._responder is not None:
            return self._responder(system, messages)
        if self._canned is not None:
            if not self._canned:
                raise RuntimeError("FakeBrain ran out of canned replies")
            return self._canned.pop(0)
        last = messages[-1]["content"] if messages else ""
        return f"[FakeBrain reply]\n{last[:400]}"


def get_brain(name: Optional[str] = None, **kwargs) -> AgentBrain:
    """Factory. `name` defaults to env WORKSIM_BRAIN, else 'fake' (safe offline default).
    Set WORKSIM_BRAIN=anthropic to use the real LLM (needs the anthropic SDK + a key)."""
    name = (name or os.environ.get("WORKSIM_BRAIN", "fake")).lower()
    if name in ("fake", "offline", "test"):
        return FakeBrain(**kwargs)
    if name in ("anthropic", "claude", "llm"):
        from worksim.brain.llm import AnthropicBrain  # lazy: SDK optional
        return AnthropicBrain(**kwargs)
    raise ValueError(f"unknown brain {name!r} (use 'fake' or 'anthropic')")
