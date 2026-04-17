"""
Log Dominate Variant - Gleaner with emphasis on log-based anomaly scoring

Features:
- Increased weights for log-level anomalies (ERROR/SEVERE and WARN)
- Reduced weights for status errors and latency P90 outliers
- Useful during log analysis campaigns or when debugging log patterns

This variant shifts sampling focus to prioritize traces with suspicious
log patterns, effectively "zooming in" on log-based anomalies.
"""

from typing import List

from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SampleResult, SamplerArgs

from ..core.sampler import GleanerSampler
from ..utils.config import (
    LOG_DOMINATE_ANOMALY_CONFIG,
    GleanerConfig,
)


class LogDominateVariant(GleanerSampler):
    """
    Gleaner variant with log-dominated anomaly scoring

    Features:
    - Higher weights for log-level anomalies
    - Lower weights for status errors and latency
    - Full alarm system and quota allocation
    """

    def __init__(self):
        """Initialize with log-dominate anomaly score config"""
        config = GleanerConfig(
            anomaly_score=LOG_DOMINATE_ANOMALY_CONFIG,
        )
        super().__init__(config)
        logger.info(
            "Initialized Log Dominate Variant "
            f"(log_error={LOG_DOMINATE_ANOMALY_CONFIG.log_error_weight}, "
            f"log_warn={LOG_DOMINATE_ANOMALY_CONFIG.log_warning_weight}, "
            f"status_error={LOG_DOMINATE_ANOMALY_CONFIG.status_error_weight})"
        )

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant with log-dominated scoring"""
        logger.info(
            f"=== Gleaner Log-Dominate Variant: {args.dataset}/{args.datapack} ==="
        )
        logger.info("Using log-dominated anomaly scoring for log analysis focus")

        # Use parent implementation with modified config
        return super().__call__(args)
