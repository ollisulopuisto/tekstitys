from PySide6.QtGui import QKeySequence

from app.views.main_window import MainWindow


def _menu_actions(window):
    for menu_action in window.menuBar().actions():
        for action in menu_action.menu().actions():
            if not action.isSeparator():
                yield action


def _find(window, text):
    return next(a for a in _menu_actions(window) if a.text() == text)


def test_standard_mac_shortcuts_are_in_the_menus(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    def native(key):
        return QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)

    expected = {
        "Open Video…": QKeySequence.StandardKey.Open,
        "Save Project": QKeySequence.StandardKey.Save,
        "Close Window": QKeySequence.StandardKey.Close,
        "Quit Tekstitys": QKeySequence.StandardKey.Quit,
        "Zoom In": QKeySequence.StandardKey.ZoomIn,
        "Zoom Out": QKeySequence.StandardKey.ZoomOut,
        "Transcription Settings…": QKeySequence.StandardKey.Preferences,
    }
    for text, key in expected.items():
        assert _find(window, text).shortcut().toString(
            QKeySequence.SequenceFormat.NativeText
        ) == native(key), text


def test_a_menu_item_presses_its_button_only_while_it_is_enabled(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    presses = []
    window.save_btn.clicked.connect(lambda: presses.append("save"))

    window.save_btn.setEnabled(False)
    _find(window, "Save Project").trigger()
    assert presses == []

    window.save_btn.setEnabled(True)
    _find(window, "Save Project").trigger()
    assert presses == ["save"]


def _menu(window, title):
    return next(a.menu() for a in window.menuBar().actions() if a.text() == title)


def test_window_menu_minimizes_and_closes_the_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    win = _menu(window, "Window")
    acts = {a.text(): a for a in win.actions() if not a.isSeparator()}
    assert "Minimize" in acts, list(acts)
    assert "Close Window" in acts, list(acts)
    assert acts["Minimize"].shortcut() == QKeySequence("Ctrl+M")
    assert acts["Close Window"].shortcut() == QKeySequence(
        QKeySequence.StandardKey.Close
    )
    assert not window.isMinimized()
    acts["Minimize"].trigger()
    assert window.isMinimized()


def test_close_window_lives_under_window_not_file(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    file_texts = [a.text() for a in _menu(window, "File").actions()]
    assert "Close Window" not in file_texts


def test_edit_menu_cut_copy_paste_select_all_on_the_focused_widget(qtbot):
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication, QLineEdit

    window = MainWindow()
    qtbot.addWidget(window)
    # Created before show(): a widget that is still hidden cannot take focus,
    # and focus then stays on whatever the window gave it to (the timeline).
    edit = QLineEdit(window)
    edit.setText("hello")
    window.show()
    window.activateWindow()
    edit.setFocus()
    qtbot.waitUntil(lambda: QApplication.focusWidget() is edit)

    _find(window, "Select All").trigger()
    assert edit.selectedText() == "hello"
    _find(window, "Copy").trigger()
    assert QGuiApplication.clipboard().text() == "hello"
    _find(window, "Cut").trigger()
    assert edit.text() == ""
    _find(window, "Paste").trigger()
    assert edit.text() == "hello"

    edit.clearFocus()
    # Focus may fall back to another widget instead of None; either way the
    # line edit must not change and nothing may crash.
    _find(window, "Paste").trigger()
    assert edit.text() == "hello"
