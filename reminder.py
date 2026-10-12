"""Мягкое окно-напоминание о перерыве — строгий стиль."""

from __future__ import annotations

import winsound
from typing import Callable

import customtkinter as ctk

from theme import COLORS, RADIUS, font, title_font


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
        self._total = max(1, break_seconds)
        self._remaining = break_seconds
        self._closed = False
        self._tick_job: str | None = None

        self.title("Break Point — перерыв")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._skip)

        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=0, padx=14, pady=14, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="ПЕРЕРЫВ",
            font=font(11, "bold"),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, padx=18, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            card,
            text="Пора отдохнуть",
            font=title_font(24),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, padx=18, pady=(0, 6), sticky="ew")

        self.message_label = ctk.CTkLabel(
            card,
            text=message,
            wraplength=360,
            justify="left",
            anchor="w",
            font=font(13),
            text_color=COLORS["text_muted"],
        )
        self.message_label.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")

        self.countdown_label = ctk.CTkLabel(
            card,
            text=self._format_time(self._remaining),
            font=title_font(42),
            text_color=COLORS["accent"],
        )
        self.countdown_label.grid(row=3, column=0, padx=18, pady=(2, 6))

        self.progress = ctk.CTkProgressBar(
            card,
            height=4,
            corner_radius=RADIUS,
            progress_color=COLORS["accent"],
            fg_color=COLORS["ghost"],
        )
        self.progress.grid(row=4, column=0, padx=18, pady=(0, 4), sticky="ew")
        self.progress.set(1.0)

        ctk.CTkLabel(
            card,
            text="осталось до конца перерыва",
            font=font(11),
            text_color=COLORS["text_muted"],
        ).grid(row=5, column=0, padx=18, pady=(0, 14))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=6, column=0, padx=14, pady=(0, 16), sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            buttons,
            text="Отдохнул",
            height=36,
            corner_radius=RADIUS,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(13, "bold"),
            command=self._done,
        ).grid(row=0, column=0, columnspan=2, padx=3, pady=(0, 6), sticky="ew")

        ctk.CTkButton(
            buttons,
            text=f"Ещё {snooze_minutes} мин",
            height=32,
            corner_radius=RADIUS,
            fg_color=COLORS["ghost"],
            hover_color=COLORS["ghost_hover"],
            text_color=COLORS["ghost_text"],
            font=font(12, "bold"),
            border_width=1,
            border_color=COLORS["border"],
            command=self._snooze,
        ).grid(row=1, column=0, padx=(3, 3), sticky="ew")
        ctk.CTkButton(
            buttons,
            text="Пропустить",
            height=32,
            corner_radius=RADIUS,
            fg_color=COLORS["ghost"],
            hover_color=COLORS["ghost_hover"],
            text_color=COLORS["skip_hover"],
            font=font(12, "bold"),
            border_width=1,
            border_color=COLORS["border"],
            command=self._skip,
        ).grid(row=1, column=1, padx=(3, 3), sticky="ew")

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
        self.progress.set(self._remaining / self._total)
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
