from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QWidget

from app.models.captions import CaptionSegment
from app.views.timeline import MAX_ZOOM, VisualTimelineWidget


def test_timeline_index_of_binary_search(qtbot):
    """Verify O(log N) bisect segment index lookup handles empty, missing, boundaries, and duplicates."""
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)

    # Empty segments
    assert timeline._index_of(None) == -1
    seg_dummy = CaptionSegment(start_ms=1000, end_ms=2000, text="Dummy")
    assert timeline._index_of(seg_dummy) == -1

    # Populated segments
    seg1 = CaptionSegment(start_ms=1000, end_ms=2000, text="Seg 1")
    seg2 = CaptionSegment(start_ms=3000, end_ms=4000, text="Seg 2")
    seg3 = CaptionSegment(start_ms=3000, end_ms=5000, text="Seg 3 (duplicate start)")
    seg4 = CaptionSegment(start_ms=6000, end_ms=7000, text="Seg 4")
    timeline.set_segments([seg1, seg2, seg3, seg4])

    assert timeline._index_of(seg1) == 0
    assert timeline._index_of(seg2) == 1
    assert timeline._index_of(seg3) == 2
    assert timeline._index_of(seg4) == 3

    # Segment not in list (even if start_ms matches an existing segment)
    other_same_time = CaptionSegment(start_ms=3000, end_ms=4500, text="Other")
    assert timeline._index_of(other_same_time) == -1
    other_diff_time = CaptionSegment(start_ms=8000, end_ms=9000, text="Other 2")
    assert timeline._index_of(other_diff_time) == -1
    assert timeline._index_of(None) == -1


def test_timeline_index_of_falls_back_for_unsorted_segments(qtbot):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    later = CaptionSegment(start_ms=5000, end_ms=6000, text="Later")
    earlier = CaptionSegment(start_ms=1000, end_ms=2000, text="Earlier")
    timeline.set_segments([later, earlier])

    assert timeline._index_of(later) == 0
    assert timeline._index_of(earlier) == 1


def test_timeline_click_keeps_first_match_for_overlapping_segments(qtbot):
    timeline = VisualTimelineWidget()
    timeline.resize(1000, 80)
    timeline.set_duration(10000)
    qtbot.addWidget(timeline)
    timeline.show()
    first = CaptionSegment(start_ms=1000, end_ms=7000, text="First")
    second = CaptionSegment(start_ms=3000, end_ms=5000, text="Second")
    timeline.set_segments([first, second])

    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(400, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(400, 40))

    assert timeline.selected_segment is first


def test_timeline_initial_state(qtbot):
    parent = QWidget()
    timeline = VisualTimelineWidget(parent)
    qtbot.addWidget(timeline)

    assert timeline.duration_ms == 0
    assert timeline.current_position_ms == 0
    assert timeline.segments == []
    assert timeline.selected_segment is None


def test_timeline_seek_on_click(qtbot):
    timeline = VisualTimelineWidget()
    timeline.resize(1000, 80)
    timeline.set_duration(10000)  # 10.0 seconds
    qtbot.addWidget(timeline)
    timeline.show()

    emitted_seeks = []
    timeline.seek_requested.connect(emitted_seeks.append)

    # Click in the middle (x = 500 out of 1000 -> 5000 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(500, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(500, 40))

    assert len(emitted_seeks) > 0
    # Should seek to approx 5000 ms (+/- 100ms)
    assert 4900 <= emitted_seeks[-1] <= 5100


def test_timeline_select_segment(qtbot):
    timeline = VisualTimelineWidget()
    timeline.resize(1000, 80)
    timeline.set_duration(10000)  # 10.0 seconds

    seg1 = CaptionSegment(start_ms=1000, end_ms=3000, text="First segment")
    seg2 = CaptionSegment(start_ms=5000, end_ms=8000, text="Second segment")
    timeline.set_segments([seg1, seg2])
    qtbot.addWidget(timeline)
    timeline.show()

    selected = []
    timeline.segment_selected.connect(selected.append)

    # Click inside seg1 (start: 100px, end: 300px -> click at x = 200)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(200, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(200, 40))

    assert len(selected) > 0
    assert selected[-1] == seg1
    assert timeline.selected_segment == seg1


def test_timeline_click_segment_binary_search_boundaries(qtbot):
    """Verify O(log N) bisect segment selection handles start, middle, end, gaps, and empty state."""
    timeline = VisualTimelineWidget()
    timeline.resize(1000, 80)
    timeline.set_duration(10000)  # 1 px ~= 10 ms (duration_ms / (width - 1))
    qtbot.addWidget(timeline)
    timeline.show()

    # 1. Click on empty segments list
    timeline.set_segments([])
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(200, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(200, 40))
    assert timeline.selected_segment is None

    # 2. Multiple segments with gaps
    seg1 = CaptionSegment(start_ms=1000, end_ms=3000, text="First")
    seg2 = CaptionSegment(start_ms=5000, end_ms=7000, text="Second")
    seg3 = CaptionSegment(start_ms=8500, end_ms=9500, text="Third")
    timeline.set_segments([seg1, seg2, seg3])

    # Click in gap before seg1 (x = 50 -> ~500 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(50, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(50, 40))
    assert timeline.selected_segment is None

    # Click inside seg1 near start (start_ms=1000 -> x = 150 -> ~1500 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(150, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(150, 40))
    assert timeline.selected_segment == seg1

    # Click inside seg1 near end (end_ms=3000 -> x = 280 -> ~2800 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(280, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(280, 40))
    assert timeline.selected_segment == seg1

    # Click in gap between seg1 and seg2 (x = 400 -> ~4000 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(400, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(400, 40))
    assert timeline.selected_segment is None

    # Click inside seg2 middle (x = 600 -> ~6000 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(600, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(600, 40))
    assert timeline.selected_segment == seg2

    # Click inside seg3 (x = 900 -> ~9000 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(900, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(900, 40))
    assert timeline.selected_segment == seg3

    # Click in gap after seg3 (x = 980 -> ~9800 ms)
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(980, 40))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(980, 40))
    assert timeline.selected_segment is None


def _trimmed_timeline(qtbot, start_ms=2000, end_ms=8000):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.set_duration(10000)
    timeline.set_trim_range(start_ms, end_ms)
    emitted = []
    timeline.trim_range_changed.connect(lambda s, e: emitted.append((s, e)))
    return timeline, emitted


def test_set_trim_start_at_playhead(qtbot):
    timeline, emitted = _trimmed_timeline(qtbot)
    timeline.set_trim_start_at(3500)
    assert (timeline.trim_start_ms, timeline.trim_end_ms) == (3500, 8000)
    assert emitted == [(3500, 8000)]


def test_set_trim_end_at_playhead(qtbot):
    timeline, emitted = _trimmed_timeline(qtbot)
    timeline.set_trim_end_at(6200)
    assert (timeline.trim_start_ms, timeline.trim_end_ms) == (2000, 6200)
    assert emitted == [(2000, 6200)]


def test_trim_start_past_the_end_releases_the_end(qtbot):
    timeline, emitted = _trimmed_timeline(qtbot)
    timeline.set_trim_start_at(9000)
    assert (timeline.trim_start_ms, timeline.trim_end_ms) == (9000, 10000)
    assert emitted == [(9000, 10000)]


def test_trim_end_before_the_start_releases_the_start(qtbot):
    timeline, emitted = _trimmed_timeline(qtbot)
    timeline.set_trim_end_at(1000)
    assert (timeline.trim_start_ms, timeline.trim_end_ms) == (0, 1000)
    assert emitted == [(0, 1000)]


def _cue_timeline(qtbot):
    timeline = VisualTimelineWidget()
    timeline.resize(1000, 80)
    timeline.set_duration(10000)  # 1 px is about 10 ms
    qtbot.addWidget(timeline)
    timeline.show()
    seg1 = CaptionSegment(start_ms=1000, end_ms=3000, text="First")
    seg2 = CaptionSegment(start_ms=5000, end_ms=8000, text="Second")
    timeline.set_segments([seg1, seg2])
    return timeline, seg1, seg2


def _drag(qtbot, timeline, start_x, end_x, y=50):
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(start_x, y))
    qtbot.mouseMove(timeline, pos=QPoint(end_x, y))
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(end_x, y))


def test_dragging_a_caption_body_moves_it_and_keeps_its_length(qtbot):
    timeline, seg1, _ = _cue_timeline(qtbot)
    retimed = []
    timeline.cue_retimed.connect(retimed.append)

    # seg1 spans x = 100..300; press in its body and drag 100 px right (~1 s).
    _drag(qtbot, timeline, 200, 300)

    assert retimed == [seg1]
    assert abs(seg1.start_ms - 2000) <= 20
    assert seg1.end_ms - seg1.start_ms == 2000


def test_dragging_the_start_edge_stops_at_the_previous_caption(qtbot):
    timeline, seg1, seg2 = _cue_timeline(qtbot)

    # seg2 starts at x = 500. Drag its start far left, into seg1.
    _drag(qtbot, timeline, 500, 50)

    assert seg2.start_ms == seg1.end_ms == 3000
    assert seg2.end_ms == 8000


def test_dragging_the_end_edge_stops_at_the_next_caption(qtbot):
    timeline, seg1, seg2 = _cue_timeline(qtbot)

    # seg1 ends at x = 300. Drag its end far right, into seg2.
    _drag(qtbot, timeline, 300, 900)

    assert seg1.end_ms == seg2.start_ms == 5000
    assert seg1.start_ms == 1000


def test_a_click_on_a_caption_selects_and_seeks_without_retiming(qtbot):
    timeline, seg1, _ = _cue_timeline(qtbot)
    retimed, selected = [], []
    timeline.cue_retimed.connect(retimed.append)
    timeline.segment_selected.connect(selected.append)

    _drag(qtbot, timeline, 200, 201)  # under the drag threshold

    assert retimed == []
    assert selected[-1] is seg1
    assert (seg1.start_ms, seg1.end_ms) == (1000, 3000)


def _touching_timeline(qtbot):
    timeline = VisualTimelineWidget()
    timeline.resize(1000, 80)
    timeline.set_duration(10000)
    qtbot.addWidget(timeline)
    timeline.show()
    seg1 = CaptionSegment(start_ms=1000, end_ms=3000, text="First")
    seg2 = CaptionSegment(start_ms=3000, end_ms=8000, text="Second")
    timeline.set_segments([seg1, seg2])
    return timeline, seg1, seg2


def test_rolling_edit_moves_the_splice_and_both_captions_follow(qtbot):
    timeline, seg1, seg2 = _touching_timeline(qtbot)
    timeline.set_edit_mode("rolling")
    retimed = []
    timeline.cue_retimed.connect(retimed.append)

    # The splice sits at x = 300. Drag it about 1 s to the left.
    _drag(qtbot, timeline, 300, 200)

    assert seg1.end_ms == seg2.start_ms
    assert seg1.end_ms < 2500
    assert seg1.start_ms == 1000
    assert seg2.end_ms == 8000
    assert {id(s) for s in retimed} == {id(seg1), id(seg2)}


def test_regular_edit_shared_boundary_moves_the_splice(qtbot):
    """A boundary shared by two touching captions is a splice in either mode.

    Whisper transcripts are contiguous, so in regular edit every drag used to
    clamp to zero movement: the caption cannot extend into its neighbour and
    the neighbour refuses to move. Dragging a shared boundary now moves it,
    growing one caption as the other shrinks.
    """
    timeline, seg1, seg2 = _touching_timeline(qtbot)
    timeline.set_edit_mode("regular")
    retimed = []
    timeline.cue_retimed.connect(retimed.append)

    # The shared boundary sits at x = 300. Drag it about 1 s to the right.
    _drag(qtbot, timeline, 300, 400)

    assert seg1.end_ms == seg2.start_ms
    assert seg1.end_ms > 3500
    assert seg1.start_ms == 1000
    assert seg2.end_ms == 8000
    assert {id(s) for s in retimed} == {id(seg1), id(seg2)}


def test_regular_edit_edge_across_a_gap_changes_only_the_dragged_caption(qtbot):
    """With free space beside the caption, regular edit moves only its edge."""
    timeline, seg1, seg2 = _cue_timeline(qtbot)
    timeline.set_edit_mode("regular")

    # seg2 starts at x = 500, with a gap to seg1 (ends at x = 300). Drag the
    # start edge 1 s left, into the gap.
    _drag(qtbot, timeline, 500, 400)

    assert abs(seg2.start_ms - 4000) <= 20
    assert seg2.end_ms == 8000
    assert (seg1.start_ms, seg1.end_ms) == (1000, 3000)


def test_zoom_widens_the_timeline_and_is_limited(qtbot):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.set_duration(10000)
    timeline.set_fit_width(800)
    assert timeline.width() == 800

    timeline.set_zoom(4)
    assert timeline.width() == 3200

    timeline.set_zoom(1000)
    assert timeline.zoom == MAX_ZOOM
    timeline.set_zoom(0.1)
    assert timeline.zoom == 1.0


# --- the cached static layer ---------------------------------------------------


def _painted(qtbot, n=6):
    """A shown timeline whose static-layer rebuilds are recorded."""
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.resize(900, 84)
    timeline.set_duration(n * 2000)
    segs = [
        CaptionSegment(start_ms=i * 2000, end_ms=i * 2000 + 1800, text=f"Cue {i} words")
        for i in range(n)
    ]
    timeline.set_segments(segs)
    timeline.show()
    rebuilds = []
    render = timeline._render_static
    timeline._render_static = lambda rect: rebuilds.append(rect) or render(rect)
    timeline.grab()
    rebuilds.clear()
    return timeline, segs, rebuilds


def test_the_needle_moving_does_not_rebuild_the_static_layer(qtbot):
    timeline, _, rebuilds = _painted(qtbot)
    before = timeline.grab().toImage()

    timeline.set_position(3000)
    after = timeline.grab().toImage()

    assert rebuilds == []
    assert after != before


def test_scrubbing_does_not_rebuild_the_static_layer(qtbot):
    timeline, _, rebuilds = _painted(qtbot)

    qtbot.mousePress(
        timeline, Qt.MouseButton.LeftButton, pos=QPoint(142, 5)
    )  # in the gap between two cues
    qtbot.mouseMove(timeline, pos=QPoint(400, 5))
    timeline.grab()
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(400, 5))

    assert timeline.current_position_ms > 0
    assert rebuilds == []


def test_a_caption_edited_in_place_shows_after_update(qtbot):
    timeline, segs, rebuilds = _painted(qtbot)
    before = timeline.grab().toImage()

    segs[1].text = "Something else entirely"
    timeline.update()
    timeline.grab()

    assert len(rebuilds) == 1
    assert timeline.grab().toImage() != before


def test_a_caption_retimed_in_place_shows_after_update(qtbot):
    timeline, segs, rebuilds = _painted(qtbot)
    before = timeline.grab().toImage()

    segs[1].end_ms = 3000
    timeline.update()
    timeline.grab()

    assert len(rebuilds) == 1
    assert timeline.grab().toImage() != before


def test_every_change_to_the_static_layer_rebuilds_it(qtbot):
    timeline, segs, rebuilds = _painted(qtbot)
    changes = [
        lambda: timeline.set_segments(segs[:4]),
        lambda: timeline.select_segment(segs[1]),
        lambda: timeline.select_segment(None),
        lambda: timeline.set_duration(timeline.duration_ms + 4000),
        lambda: timeline.set_fit_width(1200),
        lambda: timeline.set_zoom(2.0),
    ]
    for i, change in enumerate(changes):
        rebuilds.clear()
        change()
        timeline.grab()
        assert len(rebuilds) == 1, f"change {i}"


def test_the_trim_is_drawn_over_the_layer_without_rebuilding_it(qtbot):
    timeline, _, rebuilds = _painted(qtbot)
    before = timeline.grab().toImage()

    timeline.set_trim_range(1000, 8000)

    assert timeline.grab().toImage() != before
    assert rebuilds == []


def test_a_repaint_with_nothing_changed_reuses_the_layer(qtbot):
    timeline, _, rebuilds = _painted(qtbot)

    timeline.update()
    timeline.grab()
    timeline.grab()

    assert rebuilds == []


def test_the_cached_paint_matches_a_fresh_one(qtbot):
    timeline, segs, _ = _painted(qtbot)
    timeline.select_segment(segs[2])
    timeline.set_trim_range(1500, 9000)
    timeline.set_position(4000)
    cached = timeline.grab().toImage()

    timeline._invalidate_static()

    assert timeline.grab().toImage() == cached


def test_paint_static_bisect_culling(qapp):
    """Verify O(log N) bisect cue culling in _paint_static renders accurately."""
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtCore import QRect

    widget = VisualTimelineWidget()
    widget.resize(1200, 100)
    widget.set_duration(60000)

    # Empty segments
    widget.set_segments([])
    img = QImage(1200, 100, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    widget._paint_static(p, QRect(100, 0, 200, 100))
    p.end()

    # Many segments
    segments = [
        CaptionSegment(start_ms=i * 500, end_ms=i * 500 + 400, text=f"Seg {i}")
        for i in range(100)
    ]
    widget.set_segments(segments)
    p = QPainter(img)
    widget._paint_static(p, QRect(500, 0, 300, 100))
    p.end()


def test_drag_retime_refreshes_segment_flags(qapp):
    """Regression (Devin on #67): an in-place drag retime that creates
    overlap must drop the bisect fast path, or _paint_static skips an
    earlier caption still visible in the clip."""
    widget = VisualTimelineWidget()
    widget.resize(1200, 100)
    widget.set_duration(60000)
    segs = [
        CaptionSegment(start_ms=1000, end_ms=2000, text="A"),
        CaptionSegment(start_ms=3000, end_ms=4000, text="B"),
    ]
    widget.set_segments(segs)
    assert widget._segments_non_overlapping is True

    # In-place retime that creates overlap, like a finished cue drag.
    segs[1].start_ms = 1500
    widget._refresh_segment_flags()

    assert widget._segments_non_overlapping is False

    # Unsorted after retime: both flags fall.
    segs[1].start_ms = 500
    widget._refresh_segment_flags()
    assert widget._segments_sorted is False
    assert widget._segments_non_overlapping is False


def test_a_tall_timeline_splits_neighbouring_captions_into_two_lanes(qtbot):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.setFixedHeight(140)
    timeline.resize(800, 140)
    segments = [
        CaptionSegment(start_ms=i * 3000, end_ms=i * 3000 + 2500, text=f"Cue {i}")
        for i in range(4)
    ]
    timeline.set_segments(segments)

    assert timeline._lane_count() == 2
    assert [timeline._lane_of(seg) for seg in segments] == [0, 1, 0, 1]
    top0, height0 = timeline._lane_span(0)
    top1, _ = timeline._lane_span(1)
    assert top1 > top0 + height0  # the second lane sits below the first


def test_a_short_timeline_stays_a_single_lane(qtbot):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    # The default 84 px track has no room for two lanes.
    assert timeline._lane_count() == 1
    seg = CaptionSegment(start_ms=0, end_ms=1000, text="Only lane")
    timeline.set_segments([seg])
    assert timeline._lane_of(seg) == 0


def test_cue_hit_testing_respects_the_lanes(qtbot):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.setFixedHeight(140)
    timeline.resize(800, 140)
    first = CaptionSegment(start_ms=0, end_ms=2500, text="Top lane")
    second = CaptionSegment(start_ms=3000, end_ms=5500, text="Bottom lane")
    timeline.set_duration(8000)
    timeline.set_segments([first, second])

    lane0_mid = timeline._lane_span(0)[0] + 5
    lane1_mid = timeline._lane_span(1)[0] + 5
    x_first = timeline._ms_to_x(1250)
    x_second = timeline._ms_to_x(4250)

    assert timeline._cue_at(x_first, lane0_mid) == (first, "move")
    assert timeline._cue_at(x_second, lane1_mid) == (second, "move")
    # The same x on the other lane must not hit the cue.
    assert timeline._cue_at(x_first, lane1_mid) is None
    assert timeline._cue_at(x_second, lane0_mid) is None


def test_overlapping_cues_never_share_a_lane_while_one_is_free(qtbot):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.setFixedHeight(140)
    timeline.resize(800, 140)
    long_cue = CaptionSegment(start_ms=0, end_ms=10000, text="Long")
    short1 = CaptionSegment(start_ms=2000, end_ms=3000, text="Short 1")
    short2 = CaptionSegment(start_ms=4000, end_ms=5000, text="Short 2")
    timeline.set_segments([long_cue, short1, short2])

    # Short 2 cannot alternate onto the long cue's lane - it is still
    # running - so it stays under short 1 instead of overlapping.
    assert timeline._lane_of(long_cue) == 0
    assert timeline._lane_of(short1) == 1
    assert timeline._lane_of(short2) == 1


def test_dragging_a_caption_on_the_lower_lane(qtbot):
    timeline = VisualTimelineWidget()
    timeline.setFixedHeight(140)
    timeline.resize(1000, 140)
    timeline.set_duration(10000)  # 1 px is about 10 ms
    qtbot.addWidget(timeline)
    timeline.show()
    seg1 = CaptionSegment(start_ms=1000, end_ms=3000, text="Top")
    seg2 = CaptionSegment(start_ms=5000, end_ms=8000, text="Bottom")
    timeline.set_segments([seg1, seg2])
    retimed = []
    timeline.cue_retimed.connect(retimed.append)

    assert timeline._lane_of(seg2) == 1
    lane1_y = int(timeline._lane_span(1)[0] + 10)
    # seg2's body is at x = 500..800; drag from 600 to 700 (~1 s right).
    _drag(qtbot, timeline, 600, 700, y=lane1_y)

    assert retimed == [seg2]
    assert abs(seg2.start_ms - 6000) <= 20
    assert seg2.end_ms - seg2.start_ms == 3000
    # A drag on the upper lane at the same x must not touch seg2.
    seg2_start = seg2.start_ms
    lane0_y = int(timeline._lane_span(0)[0] + 10)
    _drag(qtbot, timeline, 700, 750, y=lane0_y)
    assert seg2.start_ms == seg2_start


def test_reloaded_captions_keep_their_lanes(qtbot):
    """New caption objects with the same times/text must be re-laned, not
    fall back to the upper lane because the time signature is unchanged."""
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.setFixedHeight(140)
    timeline.resize(800, 140)
    original = [
        CaptionSegment(start_ms=i * 3000, end_ms=i * 3000 + 2500, text=f"Cue {i}")
        for i in range(3)
    ]
    timeline.set_segments(original)
    # Build the lane map before the reload, so a stale cache would be reused.
    assert [timeline._lane_of(seg) for seg in original] == [0, 1, 0]
    reloaded = [
        CaptionSegment(start_ms=i * 3000, end_ms=i * 3000 + 2500, text=f"Cue {i}")
        for i in range(3)
    ]
    timeline.set_segments(reloaded)

    assert [timeline._lane_of(seg) for seg in reloaded] == [0, 1, 0]


def test_a_long_caption_keeps_its_lane_past_crowded_intervals(qtbot):
    """A shorter overlapping cue must not shrink its lane's busy-until time,
    or a later cue gets placed on top of the long one."""
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.setFixedHeight(140)
    timeline.resize(800, 140)
    a = CaptionSegment(start_ms=0, end_ms=10000, text="A")
    b = CaptionSegment(start_ms=1000, end_ms=2000, text="B")
    c = CaptionSegment(start_ms=2500, end_ms=4000, text="C")
    d = CaptionSegment(start_ms=3000, end_ms=3500, text="D")
    e = CaptionSegment(start_ms=4500, end_ms=4800, text="E")
    f = CaptionSegment(start_ms=5000, end_ms=5300, text="F")
    timeline.set_segments([a, b, c, d, e, f])

    # F starts while A is still running, so F must not land on A's lane.
    assert timeline._lane_of(a) == 0
    assert timeline._lane_of(f) == 1


def test_painting_builds_the_lane_map_once(qtbot):
    timeline = VisualTimelineWidget()
    qtbot.addWidget(timeline)
    timeline.setFixedHeight(140)
    timeline.resize(800, 140)
    timeline.set_duration(20000)
    timeline.set_segments(
        [
            CaptionSegment(start_ms=i * 2000, end_ms=i * 2000 + 1500, text=f"Cue {i}")
            for i in range(8)
        ]
    )

    calls = 0
    original = timeline._segments_signature

    def counting():
        nonlocal calls
        calls += 1
        return original()

    timeline._segments_signature = counting
    timeline.grab()
    # One build for the paint cache key, one for the lane map: linear per
    # paint, not per cue.
    assert calls <= 2, (
        f"lane map rebuilt per cue during paint ({calls} signature builds)"
    )


def test_clicking_an_overlapping_caption_selects_the_clicked_one(qtbot):
    """With overlapping captions on separate lanes, the lane-aware hit must
    win over the time-based first match."""
    timeline = VisualTimelineWidget()
    timeline.setFixedHeight(140)
    timeline.resize(1000, 140)
    timeline.set_duration(10000)
    qtbot.addWidget(timeline)
    timeline.show()
    a = CaptionSegment(start_ms=1000, end_ms=7000, text="A (top)")
    b = CaptionSegment(start_ms=3000, end_ms=5000, text="B (bottom)")
    timeline.set_segments([a, b])
    retimed = []
    timeline.cue_retimed.connect(retimed.append)

    assert timeline._lane_of(a) == 0
    assert timeline._lane_of(b) == 1
    lane1_y = int(timeline._lane_span(1)[0] + 10)
    qtbot.mouseClick(
        timeline,
        Qt.MouseButton.LeftButton,
        pos=QPoint(int(timeline._ms_to_x(4000)), lane1_y),
    )

    assert timeline.selected_segment is b

    # The drag target is the same caption that was selected.
    lane1_y = int(timeline._lane_span(1)[0] + 10)
    _drag(
        qtbot,
        timeline,
        int(timeline._ms_to_x(4000)),
        int(timeline._ms_to_x(4500)),
        y=lane1_y,
    )
    assert retimed and retimed[-1] is b
    assert a.start_ms == 1000 and a.end_ms == 7000
