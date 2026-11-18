# Caption table space fix (fix/caption-table-space)

Bug (Olli, 2026-11-18): "the caption editing is now forced into a TINY
space!" The caption table is the right column's only flexible element: the
button grid, proofreading bar, word-shift row, position card, style card and
thumbnail panel are all fixed height, so on a short window (his: ~860 px,
style section open) the table was crushed to about one row.

Fix: the table gets a floor of header + 4 rows, and the right column lives in
a QScrollArea (widgetResizable, horizontal bar off) whose inner layout uses
SetMinimumSize so its minimum tracks the content as the style section opens
and closes. Extra space still goes to the table on tall windows; short
windows scroll. The inner widget paints the window's dark background
(#0f0f11): the scroll viewport's default light Base role showed through the
gaps otherwise.

Failing-first test: test_caption_table_keeps_editing_space_on_a_short_window
(760x700 window, style section open) saw a 42 px table viewport before the
fix, 116 px after. Uses a fake core client because the Rust core binary is
not present on every host (all of test_main_window.py currently fails
without it on Linux).

Verified with offscreen window grabs at 760x700: before = one table row
visible; after = five rows plus a scrollbar. macOS GUI tests not run locally.

Follow-up in review: a QScrollArea's own minimum width is ~70 px, so the
splitter could have crushed the sidebar horizontally. The scroll area now
keeps a 320 px floor (the column's controls measure ~311 px).
