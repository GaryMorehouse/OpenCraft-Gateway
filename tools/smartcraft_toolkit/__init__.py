"""Protocol-agnostic CAN log analysis toolkit for reverse-engineering SmartCraft.

This package does not know what any byte means. It only parses candump -L
logs, groups fragmented frames into logical packets using an evidence-based
heuristic, and reports what changed. See tools/README.md for usage.
"""
