"""About Tekstitys: standard app-menu placement on macOS via AboutRole."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from app.views.main_window import MainWindow


def _find(window, text):
    for menu_action in window.menuBar().actions():
        menu = menu_action.menu()
        if menu is None:
            continue
        for action in menu.actions():
            if action.text() == text:
                return action
    raise AssertionError(f"menu item {text!r} not found")


def test_about_is_in_the_menus_with_the_about_role(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    action = _find(window, "About Tekstitys")
    # AboutRole is what moves it to the app menu on macOS.
    assert action.menuRole() == QAction.MenuRole.AboutRole


def test_about_dialog_names_the_app_and_version(qtbot, monkeypatch):
    shown = []
    monkeypatch.setattr(
        QMessageBox,
        "about",
        staticmethod(lambda _parent, title, text: shown.append((title, text))),
    )
    window = MainWindow()
    qtbot.addWidget(window)
    _find(window, "About Tekstitys").trigger()
    assert len(shown) == 1
    title, text = shown[0]
    assert title == "About Tekstitys"
    assert "Tekstitys" in text and "Version v" in text
