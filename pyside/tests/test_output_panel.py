"""The strip holds actions only; every render setting lives behind Output."""

from PySide6.QtCore import QSettings

from app.views.main_window import BUMPERS, MainWindow


def _strip_widgets(window):
    return [
        window.action_bar.itemAt(i).widget() for i in range(window.action_bar.count())
    ]


def test_strip_is_actions_then_output_then_render(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    widgets = _strip_widgets(window)
    assert widgets == [
        window.open_btn,
        window.save_btn,
        window.review_btn,
        window.broll_btn,
        window.thumb_btn,
        window.output_btn,
        window.render_btn,
    ]
    for setting in (
        window.format_combo,
        window.proof_combo,
        window.crop_combo,
        window.bumpers_btn,
        window.bug_btn,
    ):
        assert setting not in widgets


def test_output_button_opens_a_panel_with_every_render_setting(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window.output_panel
    for setting in (
        window.format_combo,
        window.proof_combo,
        window.crop_combo,
        window.bumpers_btn,
        window.bug_btn,
    ):
        assert setting.parentWidget() is panel
    assert not panel.isVisible()
    window.output_btn.click()
    assert panel.isVisible()


def test_output_summary_tracks_the_settings(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    text = window.output_btn.text()
    assert "Source" in text and "+720p" in text
    assert "No intro/outro" in text and "No logo" in text

    window.format_combo.setCurrentIndex(window.format_combo.findData("9:16"))
    assert "9:16" in window.output_btn.text()

    window.proof_combo.setCurrentIndex(window.proof_combo.findData(0))
    assert "No proof" in window.output_btn.text()

    QSettings().setValue(BUMPERS["intro"], "/tmp/channel-ident.mov")
    window._update_bumpers_button()
    assert "+ intro" in window.output_btn.text()


def test_video_menu_opens_the_output_panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    video = next(a.menu() for a in window.menuBar().actions() if a.text() == "Video")
    action = next(a for a in video.actions() if a.text() == "Output Settings…")
    assert not window.output_panel.isVisible()
    action.trigger()
    assert window.output_panel.isVisible()
