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
