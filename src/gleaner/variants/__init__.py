"""
Gleaner Variants

Implements algorithm variants as specified in requirements:
1. NoLogsVariant - no logs data
2. NoAnomalyDetectionVariant - no anomaly detection (alarm system)
3. NoLogsNoADVariant - no logs and no anomaly detection
4. PureDiversityVariant - pure diversity sampling only
8. WLKernelVariant - Weisfeiler-Lehman kernel for graph similarity in DPP
9. NoDPPVariant - quota allocation without DPP, select by anomaly score per group
10. TopScoreVariant - direct selection by anomaly score ranking (no quota, no DPP)
11. LogDominateVariant - log-dominated anomaly scoring (higher log weights)
12. LatencyDominateVariant - latency-dominated anomaly scoring (higher latency weights)
13. NoRebalanceVariant - no budget rebalancing between normal and abnormal periods
14. AnomalyPureDiversityVariant - anomaly phase uses pure diversity (no anomaly score)
"""

from .anomaly_pure_diversity_variant import AnomalyPureDiversityVariant
from .latency_dominate_variant import LatencyDominateVariant
from .log_dominate_variant import LogDominateVariant
from .no_ad_variant import NoAnomalyDetectionVariant
from .no_dpp_variant import NoDPPVariant
from .no_logs_no_ad_variant import NoLogsNoADVariant
from .no_logs_variant import NoLogsVariant
from .no_rebalance_variant import NoRebalanceVariant
from .pure_diversity_variant import PureDiversityVariant
from .top_score_variant import TopScoreVariant
from .wl_kernel_variant import WLKernelVariant

__all__ = [
    "NoLogsVariant",
    "NoAnomalyDetectionVariant",
    "NoLogsNoADVariant",
    "PureDiversityVariant",
    "WLKernelVariant",
    "NoDPPVariant",
    "TopScoreVariant",
    "LogDominateVariant",
    "LatencyDominateVariant",
    "NoRebalanceVariant",
    "AnomalyPureDiversityVariant",
]
