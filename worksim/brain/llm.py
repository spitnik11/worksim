"""Cloud-LLM AgentBrain — Anthropic via the official SDK.

Uses the `anthropic` SDK (imported lazily so the package works without it installed).
Credentials resolve from the environment the SDK's usual way (ANTHROPIC_API_KEY or an
`ant auth login` profile) — we never read or store a key ourselves.

Model defaults to `claude-opus-5` (override with env WORKSIM_BRAIN_MODEL, e.g.
`claude-sonnet-5` or `claude-haiku-4-5` to cut cost on high-volume sim runs). Adaptive
thinking is on; `effort` maps to output_config.
"""

import os
from typing import Optional

from worksim.brain import AgentBrain, Message

DEFAULT_MODEL = "claude-opus-5"


class AnthropicBrain(AgentBrain):
    def __init__(self, model: Optional[str] = None, client=None):
        self.model = model or os.environ.get("WORKSIM_BRAIN_MODEL", DEFAULT_MODEL)
        if client is not None:
            self._client = client
        else:
            import anthropic  # lazy — optional dependency
            self._client = anthropic.Anthropic()

    def complete(self, system, messages: list[Message], *, max_tokens=8000, effort="medium") -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
        )
        if getattr(resp, "stop_reason", None) == "refusal":
            details = getattr(resp, "stop_details", None)
            raise RuntimeError(f"model refused: {getattr(details, 'category', None)}")
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
