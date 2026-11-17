"""Regression coverage for source-order position overrides, without Qt."""
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.models.captions import CaptionSegment, CaptionsFile, PositionOverride, ProjectState

class OverridePrecedenceTests(unittest.TestCase):
    def segment(self,start,end):
        return CaptionSegment(start_ms=start,end_ms=end,text='caption')

    def test_constructor_keeps_unsorted_override_precedence(self):
        project=ProjectState(position_overrides=[PositionOverride(2000,3000,60),PositionOverride(0,1000,20)])
        self.assertEqual(project.get_anchor_y_for_segment(self.segment(2000,3000)),60)

    def test_wide_plus_inner_keeps_first_match_at_and_after_overlap(self):
        project=ProjectState(position_overrides=[PositionOverride(0,10000,10),PositionOverride(2000,3000,90)])
        for start,end in [(2000,3000),(4000,5000),(7000,9000)]:
            self.assertEqual(project.get_anchor_y_for_segment(self.segment(start,end)),10)

    def test_load_preserves_serialized_precedence(self):
        import tempfile
        overrides=[PositionOverride(1000,4000,60),PositionOverride(0,2000,20)]
        source=CaptionsFile(position_overrides=overrides)
        with tempfile.TemporaryDirectory() as directory:
            path=pathlib.Path(directory)/'captions.json'
            path.write_text(source.to_json_str())
            project=ProjectState()
            self.assertTrue(project.load_sidecar(path))
            self.assertEqual(project.position_overrides,overrides)
            self.assertEqual(project.get_anchor_y_for_segment(self.segment(1000,2000)),60)

    def test_retime_reposition_and_split_keep_export_precedence(self):
        project=ProjectState(position_overrides=[PositionOverride(0,2000,20)])
        project.set_segment_position_override(self.segment(1000,4000),60)
        self.assertEqual(project.get_anchor_y_for_segment(self.segment(1000,2000)),20)

if __name__=='__main__':unittest.main()
