"""Загрузка и сохранение настроек Break Point."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


APP_NAME = "Break_Point"

DEFAULTS: dict[str, Any] = {
    "work_interval_minutes": 60,
    "break_duration_minutes": 5,
    "snooze_minutes": 5,
    "message": "Пора сделать перерыв: встаньте, разомнитесь, отдохните глазами.",
    "sound_enabled": True,
    "autostart": False,
    "show_settings_on_startup": False,
}


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    data = deepcopy(DEFAULTS)
    if not path.exists():
        save_config(data)
        return data

    try:
        with path.open("r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, dict):
            data.update({k: loaded[k] for k in DEFAULTS if k in loaded})
    except (OSError, json.JSONDecodeError):
        pass

    data = _sanitize(data)
    return data


def save_config(data: dict[str, Any]) -> None:
    clean = _sanitize({**DEFAULTS, **data})
    path = config_path()
    with path.open("w", encoding="utf-8") as fh:
        json.dump(clean, fh, ensure_ascii=False, indent=2)


def _sanitize(data: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(DEFAULTS)
    result["work_interval_minutes"] = _clamp_int(
        data.get("work_interval_minutes"), 1, 480, DEFAULTS["work_interval_minutes"]
    )
    result["break_duration_minutes"] = _clamp_int(
        data.get("break_duration_minutes"), 1, 120, DEFAULTS["break_duration_minutes"]
    )
    result["snooze_minutes"] = _clamp_int(
        data.get("snooze_minutes"), 1, 60, DEFAULTS["snooze_minutes"]
    )
    message = data.get("message", DEFAULTS["message"])
    result["message"] = str(message).strip() or DEFAULTS["message"]
    result["sound_enabled"] = bool(data.get("sound_enabled", DEFAULTS["sound_enabled"]))
    result["autostart"] = bool(data.get("autostart", DEFAULTS["autostart"]))
    result["show_settings_on_startup"] = bool(
        data.get("show_settings_on_startup", DEFAULTS["show_settings_on_startup"])
    )
    return result


def _clamp_int(value: Any, minimum: int, maximum: int, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, number))
