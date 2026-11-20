# Timeline shared-splice fix (fix/timeline-shared-splice)

Bug: with a contiguous transcript (every caption touching its neighbours,
which is what Whisper produces), Regular edit could not retime anything:
body moves were boxed in by both neighbours, and a shared boundary drag
clamped to zero in the direction that would extend into the neighbour.
Reproduced with QTest (standalone widget) and pinned in
test_regular_edit_shared_boundary_moves_the_splice (failed before the fix:
the boundary stayed at 3000 ms after a +1 s drag).

Fix: `_roll_partner` no longer gates on `edit_mode == "rolling"` — a shared
boundary is a splice in either mode, since captions cannot overlap and the
drag has no other meaning. The old
test_regular_edit_changes_only_the_caption_whose_edge_is_dragged asserted the
broken zero-movement behaviour; it was replaced by
test_regular_edit_edge_across_a_gap_changes_only_the_dragged_caption, which
keeps the coverage it actually meant: an edge dragged across free space moves
only the dragged caption. The Regular edit tooltip now says a shared boundary
moves both sides.

Known follow-up (not in this PR): Regular and Rolling now behave identically
on shared boundaries; the toggle's remaining distinction is nil for touching
transcripts. Decide the toggle's fate with the UI redesign (give Rolling a
ripple meaning or drop it).

Tests: pyside/tests/test_timeline.py 29 passed (offscreen). GUI on macOS not
run locally.

---

# Caption chunking (feat/caption-chunking)

Olli, 2026-11-18: "we should break up the whisper captions into smaller
chunks, like max dunno 6 words a block?" Approved defaults: split at
punctuation/pauses, hard cap 6 words, editable in settings.

New chunk_long_segments() in the captions model splits any cue over the cap:
the latest sentence-ending punctuation inside the cap wins; without
punctuation the cut goes to the longest pause between words (ties favour the
latest cut, so even spacing fills the cap); neither present, the cue is cut
at the cap. Cues without word timings get even spans first so every chunk
keeps its place in the audio. break_after stays on the last chunk only.

Wired into the transcription pipeline in MainWindow after
combine_separated_syllables/apply_orphan_rules. The cap lives in
QSettings transcription/max_caption_words (default 6) with a spin box (2-20)
in the Orukeet/Transcription settings dialog.

7 new tests in test_captions_model.py (punctuation split, pause split, hard
cap, untouched short cues, interpolated timings, break_after placement,
custom cap). Full suite: 49 failures, all pre-existing on clean main in this
environment (no Rust core binary, portal/macOS deps); none new. ruff clean.

Review fixes (head 9ebb8bb findings, Devin agreed on the first two):
1. The pause search now also considers the pause right after the word at the
   cap, so a full-size block is cut there instead of one word early.
2. A cut never lands after a Finnish orphan word (FINNISH_ORPHAN_WORDS, the
   same list apply_orphan_rules uses): the conjunction starts the next chunk.
3. The max-words spin box has a test (default, 2-20 bounds, persistence).

---

# Sidebar tabs (feat/sidebar-tabs)

Olli picked sketch D (2026-11-18, "d"): the guided flow as tabs across the
top. The right column's stacked sections (header grid, caption table, word
shift, position card, collapsible style card, thumbnail panel) could squeeze
each other - the caption table most of all - and the mix made the app hard
to learn.

Build: a QTabBar + QStackedLayout replace the single column. Every widget
keeps its name, signals, tooltips and accessible names; only placement
changed:

- 1 Transcribe: Transcribe button, backend/style combos, Orukeet settings,
  Fix Syllables, Group Words, Finnish proofreading.
- 2 Edit (home tab): the caption table at full panel height, Adjust words
  row, Add / Fix Orphans / Save.
- 3 Style: preset, font, size, colours and checkboxes; the old collapsible
  toggle is gone (the tab is the collapse). Badge: current preset.
- 4 Position: Auto Dodge, Top/Mid/Bot, Apply to All, anchor slider, safe
  zones. Badge: current anchor %.
- 5 Thumbnail: the thumbnail panel moved here from the column bottom
  (main_window hands it to caption_panel.add_thumbnail_tab).

The strip between tab bar and pages stays visible in every tab: selected
caption timing, and proofreading counts by category (red spelling, amber
grammar, blue style) when the proofreader has results. It refreshes on
selection, playhead and proofreader changes.

Tests: the collapsible-toggle test was replaced by tab tests - five tabs and
their order, Edit as home, only the current page visible, strip content in
every tab, proofreading counts, badge values. Verified visually with
offscreen grabs of all five tabs at 1280x800. macOS GUI not run locally.

Devin finding (fixed): the strip cached the selected cue's timestamps, so a
timecode edit or timeline drag left stale times when the cue object was
unchanged. _retime_segment and cue_moved_on_timeline now refresh the strip;
a test pins both paths.

Review follow-up: added a reachability test that walks every action button
of the pre-tabs header (Transcribe, Orukeet, Add, Auto Dodge, Fix Syllables,
Group Words, Fix Orphans, Save, In/Out, both Shifts, Delete Empty) up its
parent chain and asserts it lands on a tab page, then switches to that tab
and asserts the button is visible. Guards the tabs rebuild against creating
a control but never placing it.

Wide-screen layout (sketch G, picked 2026-11-18): the right sidebar is
capped at 560 px (right_widget.setMaximumWidth), so on a wide window the
video preview grows instead of the controls spreading. The timeline leaves
the left column and docks full width below the splitter, 140 px tall, with
its edit-mode/zoom toolbar above it. When the track is tall enough
(2 x 40 px lanes + gap) it splits into two lanes, neighbouring captions
alternating lanes; hit testing respects the lane under the pointer. A short
timeline stays single-lane, so narrow windows are unchanged.

Tests: lane split, single-lane fallback, lane-aware hit testing
(test_timeline.py); dock placement and the 560 px cap
(test_main_window.py, MockCore). Verified visually with an offscreen grab
at 1920x1080: sidebar capped, preview wide, two-lane timeline across the
bottom. macOS GUI not run locally.
Review follow-up (Olli, 2026-11-18): the action tiles spread across the wide
left column in a 3-column grid. The action bar is now the existing
FlowLayout - one compact row when the column is wide, wrapping onto more
rows only when narrow. Crop combo moved after proofreading so the
B-roll/Export/proof group stays together.

Edit menu Cut/Copy/Paste investigation (Olli, 2026-11-20): he could not find
Edit > Cut/Copy/Paste/Select All while testing. Verified on main: #86 defines
them, dispatch via QApplication.focusWidget() reaches a focused QLineEdit and,
with a new regression test, the caption table's cell editor as well. The
v26.11.20.1 DMG is built by release.yml from tag v26.11.20.1, which points at
the #86 merge commit, so the packaged app contains the items. Not run on a
Mac; if they are still missing for him, suspect the running copy predates
v26.11.20.1. Real gap found: the Window menu had Minimize and Close Window
but no Zoom. Added Window > Zoom (maximize/normal toggle) with a menu test.

Top strip rebuild (sketch A, picked by Olli 2026-11-20, "yes this is good"):
the strip mixed five actions with five render settings that looked like
buttons and wrapped onto two rows. Now the strip is actions only - Open,
Save, Review, B-roll, Thumbnail - then a single Output tile whose text is a
live summary (format, proof copy, intro/outro, logo) opening one popup panel
that holds the format, crop, proof, intro/outro and logo controls; Render
stays big and last. The crop combo keeps its old semantics (offered only
when the export shape differs from the source) inside the panel, label
hiding with it. Video > Output Settings… opens the same panel. The strip
keeps the FlowLayout, so a narrow column still wraps instead of spreading.

Tests: strip order and contents, panel contents and opening from tile and
menu, summary tracking format/proof/bumper changes
(test_output_panel.py). Existing strip wrap test unchanged. Suite: same 5
failures as unmodified main in this environment (missing ffmpeg binaries,
broll animation timing, spec version fields); 497 pass. macOS GUI not run
locally.
