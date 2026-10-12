"""Таймер рабочих интервалов."""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable


class TimerState(str, Enum):
    WORKING = "working"
    WAITING_BREAK = "waiting_break"
    PAUSED = "paused"


class BreakTimer:
    """Считает время до следующего напоминания. Тики — из UI-потока."""

    def __init__(
        self,
        work_seconds: int,
        on_break_due: Callable[[], None],
        on_tick: Callable[[TimerState, int], None] | None = None,
    ) -> None:
        self.work_seconds = max(1, work_seconds)
        self.on_break_due = on_break_due
        self.on_tick = on_tick

        self.state = TimerState.WORKING
        self._remaining = float(self.work_seconds)
        self._last_ts = time.monotonic()
        self._running = False

    def start(self) -> None:
        self._running = True
        self._last_ts = time.monotonic()
        if self.state == TimerState.PAUSED:
            self.state = TimerState.WORKING
            self._remaining = float(self.work_seconds)

    def pause(self) -> None:
        if not self._running or self.state == TimerState.WAITING_BREAK:
            self.state = TimerState.PAUSED
            self._running = False
            return
        self._sync()
        self._running = False
        self.state = TimerState.PAUSED

    def resume(self) -> None:
        if self.state != TimerState.PAUSED:
            return
        self.state = TimerState.WORKING
        self._remaining = float(self.work_seconds)
        self._running = True
        self._last_ts = time.monotonic()

    def is_paused(self) -> bool:
        return self.state == TimerState.PAUSED

    def update_interval(self, work_seconds: int) -> None:
        self.work_seconds = max(1, work_seconds)
        if self.state == TimerState.WORKING and self._running:
            self._remaining = min(self._remaining, float(self.work_seconds))

    def restart_work(self) -> None:
        self.state = TimerState.WORKING
        self._remaining = float(self.work_seconds)
        self._running = True
        self._last_ts = time.monotonic()

    def snooze(self, snooze_seconds: int) -> None:
        self.state = TimerState.WORKING
        self._remaining = float(max(1, snooze_seconds))
        self._running = True
        self._last_ts = time.monotonic()

    def mark_waiting_break(self) -> None:
        self.state = TimerState.WAITING_BREAK
        self._remaining = 0
        self._running = False

    def remaining_seconds(self) -> int:
        return max(0, int(self._remaining))

    def tick(self) -> None:
        if not self._running or self.state in (TimerState.PAUSED, TimerState.WAITING_BREAK):
            if self.on_tick:
                self.on_tick(self.state, self.remaining_seconds())
            return

        self._sync()
        if self.on_tick:
            self.on_tick(self.state, self.remaining_seconds())

        if self._remaining > 0:
            return

        self.mark_waiting_break()
        self.on_break_due()

    def _sync(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_ts
        self._last_ts = now
        self._remaining = max(0.0, self._remaining - elapsed)
