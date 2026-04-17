"""
Latency Dominate Variant - Gleaner with emphasis on latency-based anomaly scoring

Features:
- Increased weights for latency P90 outlier detection
- Reduced weights for status errors and log-level anomalies
- Useful during performance optimization campaigns

This variant shifts sampling focus to prioritize traces with latency anomalies,
effectively "zooming in" on performance-related issues. Aligns with the
"Observability as Code" paradigm for dynamic tuning of sampling focus.
"""

from typing import List

from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SampleResult, SamplerArgs

from ..core.sampler import GleanerSampler
from ..utils.config import (
    LATENCY_DOMINATE_ANOMALY_CONFIG,
    GleanerConfig,
)


class LatencyDominateVariant(GleanerSampler):
    """
    Gleaner variant with latency-dominated anomaly scoring

    Features:
    - Higher weights for latency P90 outliers
    - Lower weights for status errors and log-level anomalies
    - Full alarm system and quota allocation
    """

    def __init__(self):
        """Initialize with latency-dominate anomaly score config"""
        config = GleanerConfig(
            anomaly_score=LATENCY_DOMINATE_ANOMALY_CONFIG,
        )
        super().__init__(config)
        logger.info(
            "Initialized Latency Dominate Variant "
            f"(latency_thresholds={LATENCY_DOMINATE_ANOMALY_CONFIG.latency_p90_thresholds}, "
            f"status_error={LATENCY_DOMINATE_ANOMALY_CONFIG.status_error_weight})"
        )

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant with latency-dominated scoring"""
        logger.info(
            f"=== Gleaner Latency-Dominate Variant: {args.dataset}/{args.datapack} ==="
        )
        logger.info(
            "Using latency-dominated anomaly scoring for performance analysis focus"
        )

        # Use parent implementation with modified config
        return super().__call__(args)
