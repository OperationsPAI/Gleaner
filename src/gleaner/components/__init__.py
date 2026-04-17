"""
Gleaner Components Package

Adapts existing optimized components for architecture.
"""

from .dataloader import load_data
from .trace_encoder import encode_all_traces_batch

# Re-export for V2
__all__ = [
    "load_data",
    "encode_all_traces_batch",
]
