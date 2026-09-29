from __future__ import annotations

from app.models.schemas import Category, Priority, TriageResult

_KEYWORDS: dict[Category, list[str]] = {
    Category.water: ["water", "pipe", "burst", "leak", "flood", "sewage line", "supply"],
    Category.electricity: ["electric", "wapda", "transformer", "wire", "power", "outage", "voltage"],
    Category.sanitation: ["garbage", "trash", "sewage", "drain", "waste", "smell", "sanitation"],
    Category.roads: ["road", "pothole", "street", "crack", "footpath", "traffic", "construction"],
    Category.streetlights: ["streetlight", "street light", "lamp", "pole light", "dark street"],
}

_URGENT_WORDS = ["flood", "burst", "fire", "collapse", "danger", "urgent", "injur", "electrocut"]


class RuleBasedTriage:
    name = "rules"

    async def triage(self, text: str, location: str) -> TriageResult:
        lowered = text.lower()

        best_category = Category.other
        best_hits = 0
        for category, words in _KEYWORDS.items():
            hits = sum(1 for w in words if w in lowered)
            if hits > best_hits:
                best_hits = hits
                best_category = category

        priority = Priority.high if any(w in lowered for w in _URGENT_WORDS) else (
            Priority.normal if best_hits > 0 else Priority.low
        )

        summary = text.strip().replace("\n", " ")[:137]
        if len(text.strip()) > 137:
            summary += "..."

        confidence = 0.4 if best_hits == 0 else min(0.4 + 0.15 * best_hits, 0.9)

        return TriageResult(
            category=best_category,
            priority=priority,
            summary=summary,
            confidence=confidence,
        )
