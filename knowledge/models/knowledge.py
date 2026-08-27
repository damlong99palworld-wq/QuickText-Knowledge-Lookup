from __future__ import annotations

from dataclasses import dataclass, field
import uuid

from .property import KnowledgeProperty, new_property_id


def _norm_color(value: str) -> str:
    raw = (value or "").strip()
    if raw.startswith("#") and len(raw) == 7:
        return raw.lower()
    return raw.lower() if raw else ""


def new_entry_id() -> str:
    return f"knowledge_{uuid.uuid4().hex[:10]}"


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.replace(";", ",").split(",")]
        return [p for p in parts if p]
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()] if str(value).strip() else []


@dataclass
class KnowledgeEntry:
    id: str = field(default_factory=new_entry_id)
    name: str = ""
    color: str = ""
    aliases: list[str] = field(default_factory=list)
    category: str = ""
    short_description: str = ""
    tags: list[str] = field(default_factory=list)
    properties: list[KnowledgeProperty] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "aliases": list(self.aliases),
            "category": self.category,
            "short_description": self.short_description,
            "tags": list(self.tags),
            "properties": [p.to_dict() for p in self.properties],
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> KnowledgeEntry:
        data = data or {}
        props_raw = data.get("properties") or []
        properties: list[KnowledgeProperty] = []
        if isinstance(props_raw, list):
            for item in props_raw:
                if isinstance(item, dict):
                    properties.append(KnowledgeProperty.from_dict(item))
        return cls(
            id=str(data.get("id") or new_entry_id()),
            name=str(data.get("name") or ""),
            color=_norm_color(str(data.get("color") or "")),
            aliases=_as_str_list(data.get("aliases")),
            category=str(data.get("category") or ""),
            short_description=str(data.get("short_description") or ""),
            tags=_as_str_list(data.get("tags")),
            properties=properties,
        )

    def duplicate(self) -> KnowledgeEntry:
        return KnowledgeEntry(
            id=new_entry_id(),
            name=f"{self.name} Copy".strip(),
            color=self.color,
            aliases=list(self.aliases),
            category=self.category,
            short_description=self.short_description,
            tags=list(self.tags),
            properties=[p.copy() for p in self.properties],
        )

    def searchable_text(self) -> str:
        parts = [
            self.name,
            self.category,
            self.short_description,
            " ".join(self.aliases),
            " ".join(self.tags),
        ]
        for prop in self.properties:
            parts.append(prop.name)
            parts.append(prop.value)
        return "\n".join(parts)

    def property_by_id(self, prop_id: str) -> KnowledgeProperty | None:
        for prop in self.properties:
            if prop.id == prop_id:
                return prop
        return None
