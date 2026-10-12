"""Break Point — мягкий напоминатель о перерывах в работе."""

from __future__ import annotations

import threading
from typing import Any

import customtkinter as ctk
import pystray

from autostart import set_autostart
from config import load_config
from icon_utils import create_app_icon
from reminder import ReminderWindow
from settings_ui import SettingsWindow
from timer_engine import BreakTimer, TimerState


class BreakPointApp:
    def __init__(self) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("green")

        self.config = load_config()
        set_autostart(bool(self.config.get("autostart", False)))

        self.root = ctk.CTk()
        self.root.withdraw()
        self.root.title("Break Point")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self._reminder: ReminderWindow | None = None
        self._settings: SettingsWindow | None = None
        self._status_text = "Работа"
        self._tray_icon: pystray.Icon | None = None

        self.timer = BreakTimer(
            work_seconds=int(self.config["work_interval_minutes"]) * 60,
            on_break_due=self._on_break_due,
            on_tick=self._on_tick,
        )
        self.timer.start()

        self._schedule_tick()
        self._start_tray()

        if bool(self.config.get("show_settings_on_startup", False)):
            self.root.after(200, self._open_settings)

    def run(self) -> None:
        self.root.mainloop()

    def hide_to_tray(self) -> None:
        self.root.withdraw()

    def _schedule_tick(self) -> None:
        self.root.after(250, self._tick)

    def _tick(self) -> None:
        self.timer.tick()
        self._schedule_tick()

    def _on_tick(self, state: TimerState, remaining: int) -> None:
        if state == TimerState.PAUSED:
            self._status_text = "Пауза"
        elif state == TimerState.WAITING_BREAK:
            self._status_text = "Перерыв"
        else:
            self._status_text = f"Работа {self._fmt(remaining)}"
        self._refresh_tray_title()

    def _on_break_due(self) -> None:
        self.root.after(0, self._show_reminder)

    def _show_reminder(self) -> None:
        if self._reminder is not None and self._reminder.winfo_exists():
            self._reminder.lift()
            return

        self.timer.mark_waiting_break()
        self._reminder = ReminderWindow(
            master=self.root,
            message=str(self.config["message"]),
            break_seconds=int(self.config["break_duration_minutes"]) * 60,
            snooze_minutes=int(self.config["snooze_minutes"]),
            sound_enabled=bool(self.config["sound_enabled"]),
            on_done=self._handle_done,
            on_snooze=self._handle_snooze,
            on_skip=self._handle_skip,
        )

    def _handle_done(self) -> None:
        self._reminder = None
        self.timer.restart_work()

    def _handle_snooze(self) -> None:
        self._reminder = None
        self.timer.snooze(int(self.config["snooze_minutes"]) * 60)

    def _handle_skip(self) -> None:
        self._reminder = None
        self.timer.restart_work()

    def _open_settings(self) -> None:
        if self._settings is not None and self._settings.winfo_exists():
            self._settings.lift()
            self._settings.focus_force()
            return

        self._settings = SettingsWindow(
            master=self.root,
            config=self.config,
            on_saved=self._apply_config,
        )

    def _apply_config(self, updated: dict[str, Any]) -> None:
        self.config = updated
        self.timer.update_interval(int(updated["work_interval_minutes"]) * 60)
        if self.timer.state == TimerState.WORKING and not self.timer.is_paused():
            self.timer.restart_work()

    def _toggle_pause(self) -> None:
        if self.timer.is_paused():
            self.timer.resume()
        else:
            self.timer.pause()
        self._refresh_tray_menu()

    def _quit(self) -> None:
        if self._tray_icon is not None:
            self._tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def _start_tray(self) -> None:
        image = create_app_icon(64)
        menu = self._build_tray_menu()
        self._tray_icon = pystray.Icon("BreakPoint", image, "Break Point", menu)
        thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        thread.start()

    def _build_tray_menu(self) -> pystray.Menu:
        pause_label = "Продолжить" if self.timer.is_paused() else "Пауза"
        return pystray.Menu(
            pystray.MenuItem(lambda item: self._status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Настройки", self._tray_open_settings),
            pystray.MenuItem("Напомнить сейчас", self._tray_remind_now),
            pystray.MenuItem(pause_label, self._tray_toggle_pause),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._tray_quit),
        )

    def _refresh_tray_menu(self) -> None:
        if self._tray_icon is None:
            return
        self._tray_icon.menu = self._build_tray_menu()
        try:
            self._tray_icon.update_menu()
        except Exception:
            pass

    def _refresh_tray_title(self) -> None:
        if self._tray_icon is None:
            return
        self._tray_icon.title = f"Break Point — {self._status_text}"

    def _tray_open_settings(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self._open_settings)

    def _tray_remind_now(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self._show_reminder)

    def _tray_toggle_pause(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self._toggle_pause)

    def _tray_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._quit()

    @staticmethod
    def _fmt(seconds: int) -> str:
        minutes, secs = divmod(max(0, seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


def main() -> None:
    app = BreakPointApp()
    app.run()


if __name__ == "__main__":
    main()
