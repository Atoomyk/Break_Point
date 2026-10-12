"""Окно настроек — строгий компактный стиль."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from autostart import set_autostart
from config import save_config
from theme import (
    COLORS,
    CUSTOM_EDIT_KEYS,
    HEX_RE,
    PRESET_META,
    PRESETS,
    RADIUS,
    SCHEME_ORDER,
    Stepper,
    font,
    normalize_hex,
    sanitize_custom_colors,
    title_font,
)


class SettingsWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTk,
        config: dict[str, Any],
        on_saved: Callable[[dict[str, Any]], None],
        on_scheme_changed: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._config = dict(config)
        self._on_saved = on_saved
        self._on_scheme_changed = on_scheme_changed
        self._scheme_buttons: dict[str, ctk.CTkFrame] = {}
        self._custom_entries: dict[str, ctk.CTkEntry] = {}
        self._custom_previews: dict[str, ctk.CTkFrame] = {}
        self._custom_panel: ctk.CTkFrame | None = None
        self._recreating = False

        self.title("Break Point — настройки")
        self.geometry("500x600")
        self.minsize(500, 560)
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.work_var = ctk.StringVar(value=str(self._config["work_interval_minutes"]))
        self.break_var = ctk.StringVar(value=str(self._config["break_duration_minutes"]))
        self.snooze_var = ctk.StringVar(value=str(self._config["snooze_minutes"]))
        self.sound_var = ctk.BooleanVar(value=bool(self._config["sound_enabled"]))
        self.autostart_var = ctk.BooleanVar(value=bool(self._config["autostart"]))
        self.show_settings_var = ctk.BooleanVar(
            value=bool(self._config.get("show_settings_on_startup", False))
        )
        self.scheme_var = ctk.StringVar(value=str(self._config.get("color_scheme", "arctic")))
        custom = sanitize_custom_colors(self._config.get("custom_colors"))
        self._custom_vars = {key: ctk.StringVar(value=custom[key]) for key, _ in CUSTOM_EDIT_KEYS}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 4), sticky="ew")

        ctk.CTkLabel(
            header,
            text="BREAK POINT",
            font=title_font(20),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Настройки",
            font=font(12),
            text_color=COLORS["text_muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=RADIUS,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["skip"],
        )
        body.grid(row=1, column=0, padx=16, pady=(4, 0), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        timers = self._section(body, "ТАЙМЕРЫ")
        timers.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._add_stepper_row(timers, 0, "Интервал работы", "мин", self.work_var, 1, 480)
        self._add_stepper_row(timers, 1, "Длительность перерыва", "мин", self.break_var, 1, 120)
        self._add_stepper_row(timers, 2, "Отложить", "мин", self.snooze_var, 1, 60, last=True)

        message_card = self._section(body, "СООБЩЕНИЕ")
        message_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.message_box = ctk.CTkTextbox(
            message_card,
            height=64,
            wrap="word",
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["surface"],
            text_color=COLORS["text"],
            font=font(13),
        )
        self.message_box.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.message_box.insert("1.0", self._config["message"])

        theme_card = self._section(body, "ЦВЕТОВАЯ СХЕМА")
        theme_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self._build_theme_picker(theme_card)

        options = self._section(body, "ОПЦИИ")
        options.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        self._add_switch(options, 0, "Звуковой сигнал", self.sound_var)
        self._add_switch(options, 1, "Запуск с Windows", self.autostart_var)
        self._add_switch(options, 2, "Настройки при запуске", self.show_settings_var, last=True)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=(8, 16), sticky="ew")
        footer.grid_columnconfigure((0, 1), weight=1)

        self.error_label = ctk.CTkLabel(
            footer,
            text="",
            text_color=COLORS["danger"],
            font=font(11),
            anchor="w",
            height=16,
        )
        self.error_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        ctk.CTkButton(
            footer,
            text="Отмена",
            height=36,
            corner_radius=RADIUS,
            fg_color=COLORS["ghost"],
            hover_color=COLORS["ghost_hover"],
            text_color=COLORS["ghost_text"],
            font=font(13, "bold"),
            border_width=1,
            border_color=COLORS["border"],
            command=self.destroy,
        ).grid(row=1, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            footer,
            text="Сохранить",
            height=36,
            corner_radius=RADIUS,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(13, "bold"),
            command=self._save,
        ).grid(row=1, column=1, padx=(6, 0), sticky="ew")

        self._refresh_scheme_buttons()
        self._toggle_custom_panel()
        self.after(50, self._focus)

    def _focus(self) -> None:
        self.lift()
        self.focus_force()

    def _section(self, parent: ctk.CTkBaseClass, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card,
            text=title,
            font=font(11, "bold"),
            text_color=COLORS["text_muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 4))
        return card

    def _build_theme_picker(self, parent: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        for col in range(4):
            row.grid_columnconfigure(col, weight=1)

        for index, scheme_id in enumerate(SCHEME_ORDER):
            meta = PRESET_META[scheme_id]
            accent = (
                self._custom_vars["accent"].get()
                if scheme_id == "custom"
                else PRESETS[scheme_id]["accent"]
            )
            chip = ctk.CTkFrame(
                row,
                fg_color=COLORS["surface_muted"],
                corner_radius=RADIUS,
                border_width=1,
                border_color=COLORS["border"],
                cursor="hand2",
                height=32,
            )
            chip.grid(row=0, column=index, padx=2, sticky="ew")
            chip.grid_propagate(False)
            chip.bind("<Button-1>", lambda _e, sid=scheme_id: self._select_scheme(sid))

            inner = ctk.CTkFrame(chip, fg_color="transparent")
            inner.pack(expand=True)
            inner.bind("<Button-1>", lambda _e, sid=scheme_id: self._select_scheme(sid))

            swatch = ctk.CTkFrame(
                inner,
                width=12,
                height=12,
                corner_radius=RADIUS,
                fg_color=accent,
                border_width=1,
                border_color=COLORS["border"],
            )
            swatch.pack(side="left", padx=(6, 5))
            swatch.pack_propagate(False)
            swatch.bind("<Button-1>", lambda _e, sid=scheme_id: self._select_scheme(sid))

            label = ctk.CTkLabel(
                inner,
                text=meta["title"],
                font=font(11, "bold"),
                text_color=COLORS["text"],
            )
            label.pack(side="left")
            label.bind("<Button-1>", lambda _e, sid=scheme_id: self._select_scheme(sid))

            self._scheme_buttons[scheme_id] = chip

        self._custom_panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["surface_muted"],
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["border"],
        )
        self._custom_panel.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self._custom_panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._custom_panel,
            text="СВОИ ЦВЕТА (#RRGGBB)",
            font=font(10, "bold"),
            text_color=COLORS["text_muted"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 4))

        for row_i, (key, label_text) in enumerate(CUSTOM_EDIT_KEYS, start=1):
            ctk.CTkLabel(
                self._custom_panel,
                text=label_text,
                font=font(12),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=row_i, column=0, sticky="w", padx=10, pady=2)

            entry = ctk.CTkEntry(
                self._custom_panel,
                textvariable=self._custom_vars[key],
                width=92,
                height=26,
                corner_radius=RADIUS,
                border_width=1,
                font=font(12),
            )
            entry.grid(row=row_i, column=1, sticky="e", padx=6, pady=2)
            entry.bind("<KeyRelease>", lambda _e, k=key: self._on_custom_color_edit(k))
            self._custom_entries[key] = entry

            preview = ctk.CTkFrame(
                self._custom_panel,
                width=20,
                height=20,
                corner_radius=RADIUS,
                fg_color=self._custom_vars[key].get(),
                border_width=1,
                border_color=COLORS["border"],
            )
            preview.grid(row=row_i, column=2, padx=(0, 10), pady=2)
            preview.grid_propagate(False)
            self._custom_previews[key] = preview

        ctk.CTkButton(
            self._custom_panel,
            text="Применить цвета",
            height=30,
            corner_radius=RADIUS,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(12, "bold"),
            command=self._apply_custom_live,
        ).grid(
            row=len(CUSTOM_EDIT_KEYS) + 1,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=10,
            pady=(6, 10),
        )

    def snapshot_draft(self) -> dict[str, Any]:
        scheme = self.scheme_var.get()
        custom = sanitize_custom_colors(self._config.get("custom_colors"))
        if scheme == "custom":
            collected = self._collect_custom_colors(show_error=False)
            if collected is not None:
                custom = collected

        return {
            "work_interval_minutes": self.work_var.get().strip(),
            "break_duration_minutes": self.break_var.get().strip(),
            "snooze_minutes": self.snooze_var.get().strip(),
            "message": self.message_box.get("1.0", "end").strip() or self._config["message"],
            "sound_enabled": bool(self.sound_var.get()),
            "autostart": bool(self.autostart_var.get()),
            "show_settings_on_startup": bool(self.show_settings_var.get()),
            "color_scheme": scheme,
            "custom_colors": custom,
        }

    def _select_scheme(self, scheme_id: str) -> None:
        if scheme_id == self.scheme_var.get() and scheme_id != "custom":
            return
        self.scheme_var.set(scheme_id)
        self._emit_scheme_change()

    def _apply_custom_live(self) -> None:
        self.scheme_var.set("custom")
        colors = self._collect_custom_colors(show_error=True)
        if colors is None:
            return
        self._emit_scheme_change()

    def _emit_scheme_change(self) -> None:
        if self._on_scheme_changed is None or self._recreating:
            self._refresh_scheme_buttons()
            self._toggle_custom_panel()
            return
        draft = self.snapshot_draft()
        self._recreating = True
        self._on_scheme_changed(draft)

    def _refresh_scheme_buttons(self) -> None:
        selected = self.scheme_var.get()
        for scheme_id, chip in self._scheme_buttons.items():
            if scheme_id == selected:
                chip.configure(border_color=COLORS["accent"], fg_color=COLORS["accent_soft"])
            else:
                chip.configure(border_color=COLORS["border"], fg_color=COLORS["surface_muted"])

    def _toggle_custom_panel(self) -> None:
        if self._custom_panel is None:
            return
        if self.scheme_var.get() == "custom":
            self._custom_panel.grid()
        else:
            self._custom_panel.grid_remove()

    def _on_custom_color_edit(self, key: str) -> None:
        self._update_preview(key)

    def _update_preview(self, key: str) -> None:
        preview = self._custom_previews.get(key)
        if preview is None:
            return
        value = self._custom_vars[key].get().strip()
        if HEX_RE.match(value):
            preview.configure(fg_color=normalize_hex(value, COLORS["accent"]))

    def _add_stepper_row(
        self,
        parent: ctk.CTkFrame,
        row: int,
        title: str,
        unit: str,
        variable: ctk.StringVar,
        minimum: int,
        maximum: int,
        last: bool = False,
    ) -> None:
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.grid(row=row + 1, column=0, sticky="ew", padx=12, pady=(0, 8 if last else 4))
        block.grid_columnconfigure(0, weight=1)

        texts = ctk.CTkFrame(block, fg_color="transparent")
        texts.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            texts, text=title, font=font(13, "bold"), text_color=COLORS["text"], anchor="w"
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            texts, text=unit, font=font(11), text_color=COLORS["text_muted"], anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=(6, 0))

        Stepper(block, variable=variable, minimum=minimum, maximum=maximum).grid(
            row=0, column=1, sticky="e"
        )

    def _add_switch(
        self,
        parent: ctk.CTkFrame,
        row: int,
        title: str,
        variable: ctk.BooleanVar,
        last: bool = False,
    ) -> None:
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.grid(row=row + 1, column=0, sticky="ew", padx=12, pady=(0, 10 if last else 4))
        block.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            block, text=title, font=font(13, "bold"), text_color=COLORS["text"], anchor="w"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkSwitch(
            block,
            text="",
            variable=variable,
            width=42,
            height=20,
            progress_color=COLORS["accent"],
            button_color="#FFFFFF",
            button_hover_color="#FFFFFF",
            fg_color=COLORS["border"],
            corner_radius=RADIUS,
        ).grid(row=0, column=1, sticky="e")

    def _collect_custom_colors(self, show_error: bool = True) -> dict[str, str] | None:
        custom: dict[str, str] = {}
        for key, label in CUSTOM_EDIT_KEYS:
            raw = self._custom_vars[key].get().strip()
            if not HEX_RE.match(raw):
                if show_error:
                    self.error_label.configure(
                        text=f"Неверный цвет «{label}». Нужен формат #RRGGBB."
                    )
                return None
            custom[key] = normalize_hex(raw, COLORS[key])
        return sanitize_custom_colors(custom)

    def _save(self) -> None:
        try:
            work = int(self.work_var.get().strip())
            break_mins = int(self.break_var.get().strip())
            snooze = int(self.snooze_var.get().strip())
        except ValueError:
            self.error_label.configure(text="Введите целые числа в полях минут.")
            return

        if work < 1 or break_mins < 1 or snooze < 1:
            self.error_label.configure(text="Все интервалы должны быть не меньше 1 минуты.")
            return

        message = self.message_box.get("1.0", "end").strip()
        if not message:
            self.error_label.configure(text="Сообщение не может быть пустым.")
            return

        scheme = self.scheme_var.get()
        if scheme == "custom":
            custom_colors = self._collect_custom_colors()
            if custom_colors is None:
                return
        else:
            custom_colors = sanitize_custom_colors(self._config.get("custom_colors"))

        updated = {
            "work_interval_minutes": work,
            "break_duration_minutes": break_mins,
            "snooze_minutes": snooze,
            "message": message,
            "sound_enabled": bool(self.sound_var.get()),
            "autostart": bool(self.autostart_var.get()),
            "show_settings_on_startup": bool(self.show_settings_var.get()),
            "color_scheme": scheme,
            "custom_colors": custom_colors,
        }
        save_config(updated)
        set_autostart(updated["autostart"])
        self._on_saved(updated)
        self.destroy()
