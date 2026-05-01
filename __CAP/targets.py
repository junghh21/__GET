"""Capture target catalog.

Source of truth is `__CAP/targets.json` — edit that file (URL, selectors,
hints) and rerun the workflow. This module only loads + exposes the data.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Target:
	name: str
	url: str
	xpath: List[str] = field(default_factory=list)
	popup: Optional[str] = None
	popup_button: Optional[str] = None
	xpath_iframe: Optional[str] = None
	click: Optional[str] = None
	delay_wait: int = 0
	# Repair guidance — read by __CAP/fixer.py to inform the LLM prompt.
	goal: str = ""
	landmarks: List[str] = field(default_factory=list)
	stable_attrs: List[str] = field(default_factory=list)


CATALOG_PATH = Path(__file__).with_name("targets.json")


def _load() -> List[Target]:
	with CATALOG_PATH.open(encoding="utf-8") as f:
		data = json.load(f)
	out: List[Target] = []
	for entry in data["targets"]:
		out.append(Target(
			name=entry["name"],
			url=entry["url"],
			xpath=list(entry.get("xpath", [])),
			popup=entry.get("popup"),
			popup_button=entry.get("popup_button"),
			xpath_iframe=entry.get("xpath_iframe"),
			click=entry.get("click"),
			delay_wait=int(entry.get("delay_wait", 0)),
			goal=entry.get("goal", ""),
			landmarks=list(entry.get("landmarks", [])),
			stable_attrs=list(entry.get("stable_attrs", [])),
		))
	return out


TARGETS: List[Target] = _load()
BY_NAME: Dict[str, Target] = {t.name: t for t in TARGETS}
