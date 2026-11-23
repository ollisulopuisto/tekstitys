"""Non-blocking, replaceable frame-rate probe for frame-step controls."""

import math
import os
import shutil
from fractions import Fraction

from PySide6.QtCore import QObject, QProcess, QTimer, Signal


def parse_frame_rate(text: str) -> float | None:
    try:
        rate = float(Fraction(text.strip()))
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    return rate if math.isfinite(rate) and rate > 0 else None


def probe_command(path: str) -> tuple[str, list[str]]:
    executable = os.environ.get("FFPROBE_PATH") or shutil.which("ffprobe") or "ffprobe"
    return executable, [
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        path,
    ]


class FrameRateProbe(QObject):
    ready = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._timer = None

    def cancel(self):
        process, timer = self._process, self._timer
        self._process = self._timer = None
        if timer is not None:
            timer.stop()
        if process is not None:
            process.kill()
            # Keep it parented/alive until Qt reports completion, without a
            # blocking wait in the GUI thread. Old signals cannot apply a rate.

    def start(self, path: str):
        self.cancel()
        process = QProcess(self)
        timer = QTimer(self)
        timer.setSingleShot(True)
        self._process, self._timer = process, timer

        finished = False

        def finish(code, status):
            nonlocal finished
            if finished:
                return
            finished = True
            if self._process is process:
                self._process = self._timer = None
                timer.stop()
                if code == 0 and status == QProcess.ExitStatus.NormalExit:
                    rate = parse_frame_rate(
                        bytes(process.readAllStandardOutput()).decode(
                            "utf-8", errors="replace"
                        )
                    )
                    if rate is not None:
                        self.ready.emit(rate)
            timer.deleteLater()
            process.deleteLater()

        def error(_error):
            if process.state() == QProcess.ProcessState.NotRunning:
                finish(-1, QProcess.ExitStatus.CrashExit)

        process.finished.connect(finish)
        process.errorOccurred.connect(error)
        timer.timeout.connect(
            lambda: self.cancel() if self._process is process else None
        )
        executable, args = probe_command(path)
        process.start(executable, args)
        timer.start(5000)
