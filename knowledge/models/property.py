from __future__ import annotations

from dataclasses import dataclass, field
import uuid

from knowledge.shared.appearance import TextStyle, style_from_override_dict
from knowledge.shared.color_system import normalize_hex


def new_property_id() -> str:
    return f"prop_{uuid.uuid4().hex[:10]}"


@dataclass
class KnowledgeProperty:
    id: str = field(default_factory=new_property_id)
    name: str = ""
    value: str = ""
    style: TextStyle = field(default_factory=TextStyle)
    value_color: str = ""

    def to_dict(self) -> dict:
        data = {"id": self.id, "name": self.name, "value": self.value}
        override = self.style.to_dict(omit_empty=True)
        if self.value_color:
            override["value_color"] = normalize_hex(self.value_color)
        if override:
            data["style"] = override
        return data

    @classmethod
    def from_dict(cls, data: dict | None) -> KnowledgeProperty:
        data = data or {}
        raw_style = data.get("style") if isinstance(data.get("style"), dict) else {}
        value_color = ""
        if isinstance(raw_style, dict) and raw_style.get("value_color"):
            value_color = normalize_hex(str(raw_style.get("value_color") or ""))
        if data.get("value_color"):
            value_color = normalize_hex(str(data.get("value_color") or "")) or value_color
        return cls(
            id=str(data.get("id") or new_property_id()),
            name=str(data.get("name") or ""),
            value=str(data.get("value") or ""),
            style=style_from_override_dict(raw_style),
            value_color=value_color,
        )

    def copy(self) -> KnowledgeProperty:
        return KnowledgeProperty(
            id=new_property_id(),
            name=self.name,
            value=self.value,
            style=TextStyle(
                font_family=self.style.font_family,
                font_size=self.style.font_size,
                bold=self.style.bold,
                italic=self.style.italic,
                underline=self.style.underline,
                color=self.style.color,
            ),
            value_color=self.value_color,
        )

    def reset_style(self) -> None:
        self.style = TextStyle()
        self.value_color = ""
