"""Цветовые схемы и общие виджеты темы Break Point."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

import customtkinter as ctk

COLOR_KEYS = (
    "bg",
    "surface",
    "surface_muted",
    "border",
    "text",
    "text_muted",
    "accent",
    "accent_hover",
    "accent_soft",
    "danger",
    "ghost",
    "ghost_hover",
    "ghost_text",
    "skip",
    "skip_hover",
)

# Ключи, которые пользователь может править в «Своей» схеме.
CUSTOM_EDIT_KEYS = (
    ("bg", "Фон окна"),
    ("surface", "Карточки"),
    ("accent", "Акцент"),
    ("accent_hover", "Акцент (наведение)"),
    ("accent_soft", "Мягкий акцент"),
    ("text", "Текст"),
)

HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")

PRESETS: dict[str, dict[str, str]] = {
    "arctic": {
        "bg": "#F8F9FA",
        "surface": "#FFFFFF",
        "surface_muted": "#F1F4F8",
        "border": "#D5DEE8",
        "text": "#152033",
        "text_muted": "#64748B",
        "accent": "#6B8499",
        "accent_hover": "#547086",
        "accent_soft": "#E7EEF4",
        "danger": "#BE3A3A",
        "ghost": "#E8EEF4",
        "ghost_hover": "#D7E0EA",
        "ghost_text": "#334155",
        "skip": "#94A3B8",
        "skip_hover": "#64748B",
    },
    "coral": {
        "bg": "#F7F4F3",
        "surface": "#FFFFFF",
        "surface_muted": "#F3EDEC",
        "border": "#E5D8D6",
        "text": "#1F1716",
        "text_muted": "#7A6A67",
        "accent": "#C45C5C",
        "accent_hover": "#A84B4B",
        "accent_soft": "#F3E4E4",
        "danger": "#BE3A3A",
        "ghost": "#EFE6E4",
        "ghost_hover": "#E2D5D2",
        "ghost_text": "#4A3533",
        "skip": "#A8908C",
        "skip_hover": "#7A6A67",
    },
    "slate": {
        "bg": "#EEF2F6",
        "surface": "#FFFFFF",
        "surface_muted": "#F4F7FA",
        "border": "#D8E0EA",
        "text": "#152033",
        "text_muted": "#64748B",
        "accent": "#334155",
        "accent_hover": "#1E293B",
        "accent_soft": "#E2E8F0",
        "danger": "#BE3A3A",
        "ghost": "#E8EEF5",
        "ghost_hover": "#D9E2EC",
        "ghost_text": "#334155",
        "skip": "#94A3B8",
        "skip_hover": "#64748B",
    },
}

PRESET_META: dict[str, dict[str, str]] = {
    "arctic": {"title": "Арктика"},
    "coral": {"title": "Коралл"},
    "slate": {"title": "Сланец"},
    "custom": {"title": "Своя"},
}

SCHEME_ORDER = ("arctic", "coral", "slate", "custom")

DEFAULT_SCHEME = "arctic"

# Строгий геометричный UI без скруглений.
RADIUS = 0

# Активная палитра (обновляется при apply_scheme).
COLORS: dict[str, str] = deepcopy(PRESETS[DEFAULT_SCHEME])


def apply_app_theme() -> None:
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def normalize_hex(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not HEX_RE.match(text):
        return fallback.upper() if fallback.startswith("#") else f"#{fallback.lstrip('#').upper()}"
    if not text.startswith("#"):
        text = f"#{text}"
    return text.upper()


def darken_hex(color: str, factor: float = 0.82) -> str:
    r, g, b = _parse_rgb(color)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02X}{g:02X}{b:02X}"


def soft_tint(color: str, mix_white: float = 0.86) -> str:
    r, g, b = _parse_rgb(color)
    r = int(r + (255 - r) * mix_white)
    g = int(g + (255 - g) * mix_white)
    b = int(b + (255 - b) * mix_white)
    return f"#{r:02X}{g:02X}{b:02X}"


def _parse_rgb(color: str) -> tuple[int, int, int]:
    clean = normalize_hex(color, "#000000").lstrip("#")
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    return _parse_rgb(color)


def build_palette(scheme: str, custom_colors: dict[str, Any] | None = None) -> dict[str, str]:
    scheme_id = scheme if scheme in PRESETS or scheme == "custom" else DEFAULT_SCHEME
    if scheme_id == "custom":
        base = deepcopy(PRESETS[DEFAULT_SCHEME])
        custom = custom_colors or {}
        for key in COLOR_KEYS:
            if key in custom:
                base[key] = normalize_hex(custom[key], base[key])
        # Если hover/soft не заданы явно — выводим из акцента.
        if "accent" in custom and "accent_hover" not in custom:
            base["accent_hover"] = darken_hex(base["accent"])
        if "accent" in custom and "accent_soft" not in custom:
            base["accent_soft"] = soft_tint(base["accent"])
        return base
    return deepcopy(PRESETS[scheme_id])


def apply_scheme(scheme: str, custom_colors: dict[str, Any] | None = None) -> dict[str, str]:
    palette = build_palette(scheme, custom_colors)
    COLORS.clear()
    COLORS.update(palette)
    return palette


def apply_scheme_from_config(config: dict[str, Any]) -> dict[str, str]:
    scheme = str(config.get("color_scheme", DEFAULT_SCHEME))
    custom = config.get("custom_colors")
    if not isinstance(custom, dict):
        custom = {}
    return apply_scheme(scheme, custom)


def sanitize_custom_colors(raw: Any) -> dict[str, str]:
    base = deepcopy(PRESETS[DEFAULT_SCHEME])
    result: dict[str, str] = {}
    source = raw if isinstance(raw, dict) else {}
    for key in COLOR_KEYS:
        if key in source:
            result[key] = normalize_hex(source[key], base[key])
        else:
            result[key] = base[key]
    return result


def font(size: int = 14, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family="Bahnschrift", size=size, weight=weight)


def title_font(size: int = 26) -> ctk.CTkFont:
    return ctk.CTkFont(family="Bahnschrift", size=size, weight="bold")


class Stepper(ctk.CTkFrame):
    """Компактный контроль числа с кнопками − / +."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        variable: ctk.StringVar,
        minimum: int = 1,
        maximum: int = 480,
        width: int = 120,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface_muted"],
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )
        self.variable = variable
        self.minimum = minimum
        self.maximum = maximum

        self.grid_columnconfigure(1, weight=1)

        minus = ctk.CTkButton(
            self,
            text="−",
            width=28,
            height=28,
            corner_radius=RADIUS,
            fg_color=COLORS["ghost"],
            hover_color=COLORS["ghost_hover"],
            text_color=COLORS["text"],
            font=font(15),
            command=lambda: self._nudge(-1),
        )
        minus.grid(row=0, column=0, padx=(2, 1), pady=2)

        self.value_label = ctk.CTkLabel(
            self,
            textvariable=variable,
            width=max(32, width - 70),
            font=font(14, "bold"),
            text_color=COLORS["text"],
        )
        self.value_label.grid(row=0, column=1, padx=2, pady=2)

        plus = ctk.CTkButton(
            self,
            text="+",
            width=28,
            height=28,
            corner_radius=RADIUS,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(15),
            command=lambda: self._nudge(1),
        )
        plus.grid(row=0, column=2, padx=(1, 2), pady=2)

    def _nudge(self, delta: int) -> None:
        try:
            current = int(self.variable.get())
        except ValueError:
            current = self.minimum
        value = max(self.minimum, min(self.maximum, current + delta))
        self.variable.set(str(value))
