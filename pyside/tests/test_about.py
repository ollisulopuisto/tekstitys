"""About Tekstitys: standard app-menu placement on macOS via AboutRole."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMessageBox

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


def _fake_bundle(tmp_path, version):
    """A minimal .app layout: Contents/MacOS next to Contents/Info.plist."""
    macos = tmp_path / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    import plistlib

    with (tmp_path / "Contents" / "Info.plist").open("wb") as handle:
        plistlib.dump({"CFBundleShortVersionString": version}, handle)
    return str(macos)


def test_packaged_version_reads_the_bundle_metadata(tmp_path):
    from app.services import whatsnew

    macos = _fake_bundle(tmp_path, "26.11.20.1")
    assert whatsnew.packaged_version(macos) == "26.11.20.1"


def test_packaged_version_is_none_without_a_bundle(tmp_path):
    from app.services import whatsnew

    assert whatsnew.packaged_version(str(tmp_path)) is None


def test_about_prefers_the_packaged_version_over_the_changelog(
    qtbot, monkeypatch, tmp_path
):
    # Release CI can tag a version newer than the latest changelog heading;
    # About must show the version the user installed, not the changelog's.
    macos = _fake_bundle(tmp_path, "26.11.20.1")
    shown = []
    monkeypatch.setattr(
        QMessageBox,
        "about",
        staticmethod(lambda _parent, title, text: shown.append((title, text))),
    )
    window = MainWindow()
    qtbot.addWidget(window)
    # Patch after window creation so nothing else in startup sees the fake path.
    monkeypatch.setattr(
        QApplication, "applicationDirPath", staticmethod(lambda: macos)
    )
    changelog_version = window._whats_new_entries()[0][0]
    _find(window, "About Tekstitys").trigger()
    assert len(shown) == 1
    text = shown[0][1]
    assert "v26.11.20.1" in text
    assert changelog_version not in text
