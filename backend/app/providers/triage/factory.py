from __future__ import annotations

from app.config import get_settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage

_PROVIDERS: dict[str, type] = {
    "llm": LLMTriage,
    "ollama": OllamaTriage,
    "rules": RuleBasedTriage,
    "simulated": SimulatedTriage,
}


def get_active_provider() -> TriageProvider:
    settings = get_settings()
    key = settings.triage_provider.lower()
    provider_cls = _PROVIDERS.get(key)
    if provider_cls is None:
        raise ValueError(f"Unknown TRIAGE_PROVIDER={settings.triage_provider!r}")
    return provider_cls()


def get_fallback_provider() -> TriageProvider:
    """Always available, never fails - the safety net."""
    return RuleBasedTriage()
