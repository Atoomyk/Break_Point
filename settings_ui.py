"""Окно настроек."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from autostart import set_autostart
from config import save_config


class SettingsWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTk,
        config: dict[str, Any],
        on_saved: Callable[[dict[str, Any]], None],
    ) -> None:
        super().__init__(master)
        self._config = dict(config)
        self._on_saved = on_saved

        self.title("Break Point — настройки")
        self.geometry("480x580")
        self.minsize(480, 580)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Настройки перерывов", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(18, 8), sticky="w")

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, padx=20, pady=(4, 8), sticky="nsew")
        form.grid_columnconfigure(1, weight=1)

        self.work_var = ctk.StringVar(value=str(self._config["work_interval_minutes"]))
        self.break_var = ctk.StringVar(value=str(self._config["break_duration_minutes"]))
        self.snooze_var = ctk.StringVar(value=str(self._config["snooze_minutes"]))
        self.sound_var = ctk.BooleanVar(value=bool(self._config["sound_enabled"]))
        self.autostart_var = ctk.BooleanVar(value=bool(self._config["autostart"]))
        self.show_settings_var = ctk.BooleanVar(
            value=bool(self._config.get("show_settings_on_startup", False))
        )

        self._add_labeled_entry(form, 0, "Интервал работы (мин)", self.work_var)
        self._add_labeled_entry(form, 1, "Длительность перерыва (мин)", self.break_var)
        self._add_labeled_entry(form, 2, "Отложить на (мин)", self.snooze_var)

        ctk.CTkLabel(form, text="Сообщение").grid(
            row=3, column=0, columnspan=2, padx=12, pady=(12, 4), sticky="w"
        )
        self.message_box = ctk.CTkTextbox(form, height=90, wrap="word")
        self.message_box.grid(row=4, column=0, columnspan=2, padx=12, pady=(0, 8), sticky="ew")
        self.message_box.insert("1.0", self._config["message"])

        ctk.CTkCheckBox(form, text="Звуковой сигнал", variable=self.sound_var).grid(
            row=5, column=0, columnspan=2, padx=12, pady=(8, 6), sticky="w"
        )
        ctk.CTkCheckBox(
            form, text="Запускать вместе с Windows", variable=self.autostart_var
        ).grid(row=6, column=0, columnspan=2, padx=12, pady=6, sticky="w")
        ctk.CTkCheckBox(
            form,
            text="При запуске программы выводить окно настроек?",
            variable=self.show_settings_var,
        ).grid(row=7, column=0, columnspan=2, padx=12, pady=(6, 14), sticky="w")

        self.error_label = ctk.CTkLabel(self, text="", text_color="#d35a5a", height=18)
        self.error_label.grid(row=2, column=0, padx=20, pady=(0, 4), sticky="w")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, padx=20, pady=(4, 24), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            actions, text="Отмена", height=40, command=self.destroy, fg_color="#5a5a5a"
        ).grid(row=0, column=0, padx=6, sticky="ew")
        ctk.CTkButton(actions, text="Сохранить", height=40, command=self._save).grid(
            row=0, column=1, padx=6, sticky="ew"
        )

        self.after(50, self._focus)

    def _focus(self) -> None:
        self.lift()
        self.focus_force()

    @staticmethod
    def _add_labeled_entry(
        parent: ctk.CTkFrame, row: int, label: str, variable: ctk.StringVar
    ) -> None:
        ctk.CTkLabel(parent, text=label).grid(row=row, column=0, padx=12, pady=10, sticky="w")
        ctk.CTkEntry(parent, textvariable=variable, width=100).grid(
            row=row, column=1, padx=12, pady=10, sticky="e"
        )

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

        updated = {
            "work_interval_minutes": work,
            "break_duration_minutes": break_mins,
            "snooze_minutes": snooze,
            "message": message,
            "sound_enabled": bool(self.sound_var.get()),
            "autostart": bool(self.autostart_var.get()),
            "show_settings_on_startup": bool(self.show_settings_var.get()),
        }
        save_config(updated)
        set_autostart(updated["autostart"])
        self._on_saved(updated)
        self.destroy()
