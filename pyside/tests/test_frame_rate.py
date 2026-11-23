import pytest
from app.services.frame_rate import parse_frame_rate, probe_command


@pytest.mark.parametrize(
    "text,expected",
    [
        ("30000/1001", 30000 / 1001),
        ("25/1", 25),
        ("60", 60),
        ("0/0", None),
        ("nan", None),
        ("inf/1", None),
        ("-25/1", None),
        ("junk", None),
        ("25/0", None),
        ("25/1\n30/1", None),
    ],
)
def test_rate_validation(text, expected):
    assert parse_frame_rate(text) == expected


def test_packaged_probe(monkeypatch):
    monkeypatch.setenv("FFPROBE_PATH", "/bundle/tools/ffprobe")
    executable, args = probe_command("/tmp/a video.mp4")
    assert executable == "/bundle/tools/ffprobe"
    assert args[-1] == "/tmp/a video.mp4"
    assert "stream=avg_frame_rate" in args


def _probe_script(tmp_path):
    import sys

    script = tmp_path / "probe.py"
    script.write_text(
        'import sys,time\nif sys.argv[-1]=="slow": time.sleep(2)\nprint("24/1" if sys.argv[-1]=="slow" else "60/1")\n'
    )
    return sys.executable, [str(script)]


def test_probe_does_not_block_and_new_source_wins(qtbot, monkeypatch, tmp_path):
    from app.services import frame_rate

    executable, args = _probe_script(tmp_path)
    monkeypatch.setattr(
        frame_rate, "probe_command", lambda path: (executable, args + [path])
    )
    probe = frame_rate.FrameRateProbe()
    results = []
    probe.ready.connect(results.append)
    from PySide6.QtCore import QTimer

    ticks = []
    probe.start("slow")
    QTimer.singleShot(20, lambda: ticks.append(True))
    qtbot.waitUntil(lambda: bool(ticks), timeout=500)
    probe.start("fast")
    qtbot.waitUntil(lambda: bool(results))
    assert results == [60]
    qtbot.wait(150)
    assert results == [60]
    probe.cancel()


def test_cancel_and_missing_binary_are_silent(qtbot, monkeypatch, tmp_path):
    from app.services import frame_rate

    executable, args = _probe_script(tmp_path)
    monkeypatch.setattr(
        frame_rate, "probe_command", lambda path: (executable, args + [path])
    )
    probe = frame_rate.FrameRateProbe()
    results = []
    probe.ready.connect(results.append)
    probe.start("slow")
    probe.cancel()
    qtbot.wait(100)
    assert results == []
    monkeypatch.setattr(
        frame_rate, "probe_command", lambda path: (str(tmp_path / "absent"), [])
    )
    probe.start("anything")
    qtbot.waitUntil(lambda: probe._process is None)
    assert results == []


def test_timeout_cancels_without_emitting(qtbot, monkeypatch, tmp_path):
    from app.services import frame_rate

    executable, args = _probe_script(tmp_path)
    monkeypatch.setattr(
        frame_rate, "probe_command", lambda path: (executable, args + [path])
    )
    probe = frame_rate.FrameRateProbe()
    results = []
    probe.ready.connect(results.append)
    probe.start("slow")
    probe._timer.start(20)
    qtbot.waitUntil(lambda: probe._process is None)
    qtbot.wait(50)
    assert results == []


def test_finished_processes_are_released(qtbot, monkeypatch, tmp_path):
    from app.services import frame_rate
    from PySide6.QtCore import QProcess

    executable, args = _probe_script(tmp_path)
    monkeypatch.setattr(
        frame_rate, "probe_command", lambda path: (executable, args + [path])
    )
    probe = frame_rate.FrameRateProbe()
    for _ in range(5):
        probe.start("fast")
        qtbot.waitUntil(lambda: probe._process is None)
    qtbot.waitUntil(lambda: not probe.findChildren(QProcess))
