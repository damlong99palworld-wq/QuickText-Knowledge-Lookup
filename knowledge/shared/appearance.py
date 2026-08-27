from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from knowledge.shared.color_system import normalize_hex


STYLE_KEYS = (
    "entry_name",
    "description",
    "property_name",
    "property_value",
    "category",
    "tags",
)

WIDTHS = ("narrow", "medium", "wide", "full")
WIDTH_PX = {"narrow": 560, "medium": 720, "wide": 920, "full": 0}
LINE_SPACING = (1.0, 1.2, 1.4, 1.6)
THEMES = ("dark", "light", "system")
PRESETS = ("compact", "default", "comfortable", "large")


def _b(value, default: bool | None = None) -> bool | None:
    if value is None:
        return default
    return bool(value)


def _i(value, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _f(value, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class TextStyle:
    font_family: str = ""
    font_size: int | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    color: str = ""

    def to_dict(self, omit_empty: bool = False) -> dict:
        data = {
            "font_family": self.font_family or "",
            "font_size": self.font_size,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "color": normalize_hex(self.color),
        }
        if not omit_empty:
            return data
        out = {}
        if self.font_family:
            out["font_family"] = self.font_family
        if self.font_size is not None:
            out["font_size"] = self.font_size
        if self.bold is not None:
            out["bold"] = self.bold
        if self.italic is not None:
            out["italic"] = self.italic
        if self.underline is not None:
            out["underline"] = self.underline
        if normalize_hex(self.color):
            out["color"] = normalize_hex(self.color)
        return out

    @classmethod
    def from_dict(cls, raw: Any, defaults: "TextStyle | None" = None) -> "TextStyle":
        base = defaults or TextStyle()
        raw = raw or {}
        if not isinstance(raw, dict):
            return TextStyle(
                font_family=base.font_family,
                font_size=base.font_size,
                bold=base.bold,
                italic=base.italic,
                underline=base.underline,
                color=base.color,
            )
        family = raw.get("font_family")
        return cls(
            font_family=str(family) if family else base.font_family,
            font_size=_i(raw.get("font_size"), base.font_size),
            bold=_b(raw.get("bold"), base.bold) if "bold" in raw else base.bold,
            italic=_b(raw.get("italic"), base.italic) if "italic" in raw else base.italic,
            underline=_b(raw.get("underline"), base.underline) if "underline" in raw else base.underline,
            color=normalize_hex(str(raw.get("color") or base.color or "")),
        )

    def overlay(self, override: "TextStyle | None") -> "TextStyle":
        if override is None:
            return TextStyle(
                font_family=self.font_family,
                font_size=self.font_size,
                bold=self.bold,
                italic=self.italic,
                underline=self.underline,
                color=self.color,
            )
        return TextStyle(
            font_family=override.font_family or self.font_family,
            font_size=override.font_size if override.font_size is not None else self.font_size,
            bold=override.bold if override.bold is not None else self.bold,
            italic=override.italic if override.italic is not None else self.italic,
            underline=override.underline if override.underline is not None else self.underline,
            color=normalize_hex(override.color) or self.color,
        )

    def is_empty_override(self) -> bool:
        return not self.to_dict(omit_empty=True)


def _style(**kwargs) -> TextStyle:
    return TextStyle(**kwargs)


PRESET_STYLES = {
    "compact": {
        "entry_name": _style(font_family="Segoe UI", font_size=14, bold=True, italic=False, underline=False, color=""),
        "description": _style(font_family="Segoe UI", font_size=11, bold=False, italic=False, underline=False, color=""),
        "property_name": _style(font_family="Segoe UI", font_size=11, bold=True, italic=False, underline=False, color=""),
        "property_value": _style(font_family="Segoe UI", font_size=11, bold=False, italic=False, underline=False, color=""),
        "category": _style(font_family="Segoe UI", font_size=11, bold=False, italic=False, underline=False, color=""),
        "tags": _style(font_family="Segoe UI", font_size=11, bold=False, italic=False, underline=False, color=""),
        "line_spacing": 1.0,
        "paragraph_spacing": 4,
        "property_spacing": 8,
        "reading_width": "wide",
    },
    "default": {
        "entry_name": _style(font_family="Segoe UI", font_size=18, bold=True, italic=False, underline=False, color=""),
        "description": _style(font_family="Segoe UI", font_size=13, bold=False, italic=False, underline=False, color=""),
        "property_name": _style(font_family="Segoe UI", font_size=12, bold=True, italic=False, underline=False, color=""),
        "property_value": _style(font_family="Segoe UI", font_size=13, bold=False, italic=False, underline=False, color=""),
        "category": _style(font_family="Segoe UI", font_size=12, bold=False, italic=False, underline=False, color=""),
        "tags": _style(font_family="Segoe UI", font_size=12, bold=False, italic=False, underline=False, color=""),
        "line_spacing": 1.2,
        "paragraph_spacing": 8,
        "property_spacing": 10,
        "reading_width": "medium",
    },
    "comfortable": {
        "entry_name": _style(font_family="Segoe UI", font_size=17, bold=True, italic=False, underline=False, color=""),
        "description": _style(font_family="Segoe UI", font_size=13, bold=False, italic=False, underline=False, color=""),
        "property_name": _style(font_family="Segoe UI", font_size=13, bold=True, italic=False, underline=False, color=""),
        "property_value": _style(font_family="Segoe UI", font_size=13, bold=False, italic=False, underline=False, color=""),
        "category": _style(font_family="Segoe UI", font_size=12, bold=False, italic=False, underline=False, color=""),
        "tags": _style(font_family="Segoe UI", font_size=12, bold=False, italic=False, underline=False, color=""),
        "line_spacing": 1.4,
        "paragraph_spacing": 10,
        "property_spacing": 14,
        "reading_width": "medium",
    },
    "large": {
        "entry_name": _style(font_family="Segoe UI", font_size=20, bold=True, italic=False, underline=False, color=""),
        "description": _style(font_family="Segoe UI", font_size=16, bold=False, italic=False, underline=False, color=""),
        "property_name": _style(font_family="Segoe UI", font_size=16, bold=True, italic=False, underline=False, color=""),
        "property_value": _style(font_family="Segoe UI", font_size=16, bold=False, italic=False, underline=False, color=""),
        "category": _style(font_family="Segoe UI", font_size=14, bold=False, italic=False, underline=False, color=""),
        "tags": _style(font_family="Segoe UI", font_size=14, bold=False, italic=False, underline=False, color=""),
        "line_spacing": 1.6,
        "paragraph_spacing": 12,
        "property_spacing": 16,
        "reading_width": "narrow",
    },
}


@dataclass
class Appearance:
    entry_name: TextStyle = field(default_factory=lambda: PRESET_STYLES["default"]["entry_name"])
    description: TextStyle = field(default_factory=lambda: PRESET_STYLES["default"]["description"])
    property_name: TextStyle = field(default_factory=lambda: PRESET_STYLES["default"]["property_name"])
    property_value: TextStyle = field(default_factory=lambda: PRESET_STYLES["default"]["property_value"])
    category: TextStyle = field(default_factory=lambda: PRESET_STYLES["default"]["category"])
    tags: TextStyle = field(default_factory=lambda: PRESET_STYLES["default"]["tags"])
    line_spacing: float = 1.2
    paragraph_spacing: int = 8
    property_spacing: int = 10
    reading_width: str = "medium"
    theme: str = "dark"
    preset: str = "default"

    def to_dict(self) -> dict:
        return {
            "entry_name": self.entry_name.to_dict(),
            "description": self.description.to_dict(),
            "property_name": self.property_name.to_dict(),
            "property_value": self.property_value.to_dict(),
            "category": self.category.to_dict(),
            "tags": self.tags.to_dict(),
            "line_spacing": self.line_spacing,
            "paragraph_spacing": self.paragraph_spacing,
            "property_spacing": self.property_spacing,
            "reading_width": self.reading_width,
            "theme": self.theme,
            "preset": self.preset,
        }

    @classmethod
    def from_dict(cls, raw: Any) -> "Appearance":
        raw = raw or {}
        if not isinstance(raw, dict):
            raw = {}
        base = apply_preset("default")
        app = cls(
            entry_name=TextStyle.from_dict(raw.get("entry_name"), base.entry_name),
            description=TextStyle.from_dict(raw.get("description"), base.description),
            property_name=TextStyle.from_dict(raw.get("property_name"), base.property_name),
            property_value=TextStyle.from_dict(raw.get("property_value"), base.property_value),
            category=TextStyle.from_dict(raw.get("category"), base.category),
            tags=TextStyle.from_dict(raw.get("tags"), base.tags),
            line_spacing=_f(raw.get("line_spacing"), base.line_spacing) or 1.2,
            paragraph_spacing=_i(raw.get("paragraph_spacing"), base.paragraph_spacing) or 8,
            property_spacing=_i(raw.get("property_spacing"), base.property_spacing) or 10,
            reading_width=str(raw.get("reading_width") or base.reading_width),
            theme=str(raw.get("theme") or base.theme),
            preset=str(raw.get("preset") or "custom"),
        )
        if app.reading_width not in WIDTHS:
            app.reading_width = "medium"
        if app.theme not in THEMES:
            app.theme = "dark"
        if app.line_spacing not in LINE_SPACING:
            app.line_spacing = min(LINE_SPACING, key=lambda x: abs(x - app.line_spacing))
        app.paragraph_spacing = max(0, min(32, app.paragraph_spacing))
        app.property_spacing = max(0, min(40, app.property_spacing))
        return app

    def group(self, key: str) -> TextStyle:
        return getattr(self, key)


def apply_preset(name: str) -> Appearance:
    key = name if name in PRESET_STYLES else "default"
    spec = PRESET_STYLES[key]
    return Appearance(
        entry_name=spec["entry_name"],
        description=spec["description"],
        property_name=spec["property_name"],
        property_value=spec["property_value"],
        category=spec["category"],
        tags=spec["tags"],
        line_spacing=spec["line_spacing"],
        paragraph_spacing=spec["paragraph_spacing"],
        property_spacing=spec["property_spacing"],
        reading_width=spec["reading_width"],
        theme="dark",
        preset=key,
    )


def style_from_override_dict(raw: Any) -> TextStyle:
    raw = raw or {}
    if not isinstance(raw, dict):
        return TextStyle()
    return TextStyle(
        font_family=str(raw.get("font_family") or ""),
        font_size=_i(raw.get("font_size"), None),
        bold=_b(raw.get("bold"), None) if "bold" in raw else None,
        italic=_b(raw.get("italic"), None) if "italic" in raw else None,
        underline=_b(raw.get("underline"), None) if "underline" in raw else None,
        color=normalize_hex(str(raw.get("color") or "")),
    )


def scale_size(size: int | None, zoom: int) -> int:
    base = size or 13
    return max(8, min(48, int(round(base * (zoom / 100.0)))))
