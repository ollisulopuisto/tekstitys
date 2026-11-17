# PR 79 follow-up

Position overrides can overlap after retiming and splitting and can be passed
to the constructor out of order. Export uses first-match source order. The
unsafe bisect and sorting changes are removed, preserving serialized order.
Four regressions failed before the fix and pass afterward, including a sidecar
round trip and retime/reposition case. The proposed speedup is withdrawn.
Native PySide GUI tests were not run locally. No saved user project was opened.
