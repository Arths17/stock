"""Order intents: what the bot WANTS to do. A separate executor places them."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class OrderIntent:
    account: str
    symbol: str
    side: str            # "buy" or "sell"
    usd: float           # dollar-based order size
    signal: str          # which signal asked for it
    reason: str = ""
    paper: bool = True   # paper by default

    def to_dict(self) -> dict:
        return asdict(self)


def write_intents(intents: list[OrderIntent], path: str | Path) -> None:
    Path(path).write_text(json.dumps([i.to_dict() for i in intents], indent=2))
