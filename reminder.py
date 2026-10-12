"""Мягкое окно-напоминание о перерыве."""

from __future__ import annotations

import winsound
from typing import Callable

import customtkinter as ctk


class ReminderWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTk,
        message: str,
        break_seconds: int,
        snooze_minutes: int,
        sound_enabled: bool,
        on_done: Callable[[], None],
        on_snooze: Callable[[], None],
        on_skip: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._on_done = on_done
        self._on_snooze = on_snooze
        self._on_skip = on_skip
        self._remaining = break_seconds
        self._closed = False
        self._tick_job: str | None = None

        self.title("Break Point — перерыв")
        self.geometry("420x280")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._skip)

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Время перерыва", font=ctk.CTkFont(size=22, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(24, 8), sticky="ew")

        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            wraplength=360,
            justify="center",
            font=ctk.CTkFont(size=14),
        )
        self.message_label.grid(row=1, column=0, padx=24, pady=8, sticky="ew")

        self.countdown_label = ctk.CTkLabel(
            self,
            text=self._format_time(self._remaining),
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.countdown_label.grid(row=2, column=0, padx=20, pady=12)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, padx=16, pady=(8, 20), sticky="ew")
        buttons.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(buttons, text="Отдохнул", command=self._done).grid(
            row=0, column=0, padx=6, sticky="ew"
        )
        ctk.CTkButton(
            buttons,
            text=f"Ещё {snooze_minutes} мин",
            command=self._snooze,
            fg_color="#3a7a4a",
            hover_color="#2f643c",
        ).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(
            buttons,
            text="Пропустить",
            command=self._skip,
            fg_color="#5a5a5a",
            hover_color="#484848",
        ).grid(row=0, column=2, padx=6, sticky="ew")

        self.after(50, self._focus_and_center)
        if sound_enabled:
            self.after(80, self._beep)
        self._schedule_tick()

    def _focus_and_center(self) -> None:
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = max(40, (screen_h - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.lift()
        self.focus_force()

    def _beep(self) -> None:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def _schedule_tick(self) -> None:
        self._tick_job = self.after(1000, self._on_tick)

    def _on_tick(self) -> None:
        if self._closed:
            return
        self._remaining = max(0, self._remaining - 1)
        self.countdown_label.configure(text=self._format_time(self._remaining))
        if self._remaining <= 0:
            self._done()
            return
        self._schedule_tick()

    def _cancel_tick(self) -> None:
        if self._tick_job is not None:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None

    def _close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._cancel_tick()
        self.destroy()

    def _done(self) -> None:
        self._close()
        self._on_done()

    def _snooze(self) -> None:
        self._close()
        self._on_snooze()

    def _skip(self) -> None:
        self._close()
        self._on_skip()

    @staticmethod
    def _format_time(seconds: int) -> str:
        minutes, secs = divmod(max(0, seconds), 60)
        return f"{minutes:02d}:{secs:02d}"
