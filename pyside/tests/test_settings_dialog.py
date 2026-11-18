from PySide6.QtCore import QSettings

from app.models.captions import DEFAULT_MAX_CAPTION_WORDS
from app.views.settings_dialog import OrukeetSettingsDialog


def test_max_caption_words_spinbox_defaults_bounds_and_persists(qtbot):
    dlg = OrukeetSettingsDialog(core_client=None)
    qtbot.addWidget(dlg)

    assert dlg.max_caption_words.value() == DEFAULT_MAX_CAPTION_WORDS
    assert dlg.max_caption_words.minimum() == 2
    assert dlg.max_caption_words.maximum() == 20

    dlg.max_caption_words.setValue(9)
    assert int(QSettings().value("transcription/max_caption_words", type=int)) == 9

    # A fresh dialog reads the stored value back.
    dlg2 = OrukeetSettingsDialog(core_client=None)
    qtbot.addWidget(dlg2)
    assert dlg2.max_caption_words.value() == 9
