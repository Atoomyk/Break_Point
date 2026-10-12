"""Иконка для трея и окон."""

from __future__ import annotations

from PIL import Image, ImageDraw

from theme import COLORS, hex_to_rgb


def create_app_icon(size: int = 64, accent: str | None = None, hover: str | None = None) -> Image.Image:
    fill = hex_to_rgb(accent or COLORS["accent"])
    outline = hex_to_rgb(hover or COLORS["accent_hover"])

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = size // 10
    draw.ellipse(
        (margin, margin, size - margin, size - margin),
        fill=(*fill, 255),
        outline=(*outline, 255),
        width=max(1, size // 32),
    )

    cx = size // 2
    cy = size // 2
    hand = max(2, size // 16)
    draw.line((cx, cy, cx, margin + size // 5), fill=(255, 255, 255, 255), width=hand)
    draw.line((cx, cy, cx + size // 5, cy + size // 12), fill=(255, 255, 255, 230), width=hand)
    draw.ellipse(
        (cx - hand, cy - hand, cx + hand, cy + hand),
        fill=(255, 255, 255, 255),
    )
    return image
