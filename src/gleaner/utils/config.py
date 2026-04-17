"""
Configuration for Gleaner Algorithm
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AnomalyScoreConfig:
    """
    Configuration for anomaly score calculation hyperparameters.

    These weights are designed to be tunable parameters for dynamic adjustment
    of sampling focus. Operators can shift emphasis based on diagnostic needs:
    - During error investigations: increase status_error_weight
    - During performance optimization: increase latency weights
    - During log analysis campaigns: increase log weights

    This aligns with the "Observability as Code" paradigm.
    """

    # Status error weight (per error span in trace)
    status_error_weight: float = 5.0

    # Log level weights
    log_error_weight: float = 2.0  # Weight for ERROR/SEVERE log entries
    log_warning_weight: float = 1.0  # Weight for WARN log entries

    # Latency P90 outlier configuration
    # Each tuple is (ratio_threshold, score_value)
    # Applied in order: first matching threshold wins
    latency_p90_thresholds: List[Tuple[float, float]] = field(
        default_factory=lambda: [
            (5.0, 3.0),  # ratio >= 5.0 → score 3.0
            (3.0, 2.0),  # ratio >= 3.0 → score 2.0
            (1.5, 1.0),  # ratio >= 1.5 → score 1.0
        ]
    )


@dataclass
class GleanerConfig:
    """Configuration parameters for Gleaner algorithm"""

    # Alarm System Parameters
    warmup_duration: float = 240.0  # Warmup duration (seconds)

    # Batch Processing Parameters
    batch_size: int = 4000  # Batch size
    p90_factor: float = 1.2  # P90 anomaly judgment factor
    anomaly_weight_cap: float = 3  # Anomaly category weight cap
    p90_improvement_threshold: float = (
        2.0  # P90 improvement 200% corresponds to 1.5 weight
    )

    # DPP Algorithm Parameters
    dpp_epsilon: float = 1e-8  # DPP convergence precision
    top_k_hotspots: int = 3  # Top-K hotspot service count

    # Reproducibility
    random_seed: Optional[int] = 42  # Fixed seed for reproducible fallbacks

    # Logging & feature toggles
    log_level: str = "INFO"  # Global log level: DEBUG/INFO/WARNING/ERROR
    enable_qpm_rebalancing: bool = True  # Toggle QPM-based budget rebalancing
    enable_global_balancing: bool = True  # Toggle global quota balancing

    # Detector/Alarm System Parameters
    detector_weight: float = 3.0  # Weight multiplier for detector classes
    max_detector_budget_ratio: float = (
        0.5  # Max share of batch budget for detector classes (50%)
    )

    # Anomaly score hyperparameters (tunable for dynamic sampling focus)
    anomaly_score: AnomalyScoreConfig = field(
        default_factory=AnomalyScoreConfig
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        result = {}
        for f in self.__dataclass_fields__.values():
            val = getattr(self, f.name)
            if isinstance(val, AnomalyScoreConfig):
                result[f.name] = {
                    "status_error_weight": val.status_error_weight,
                    "log_error_weight": val.log_error_weight,
                    "log_warning_weight": val.log_warning_weight,
                    "latency_p90_thresholds": val.latency_p90_thresholds,
                }
            else:
                result[f.name] = val
        return result

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "GleanerConfig":
        """Create config from dictionary"""
        filtered = {}
        for k, v in config_dict.items():
            if k not in cls.__dataclass_fields__:
                continue
            if k == "anomaly_score" and isinstance(v, dict):
                filtered[k] = AnomalyScoreConfig(**v)
            else:
                filtered[k] = v
        return cls(**filtered)


# Default configuration instance
DEFAULT_CONFIG = GleanerConfig()


# Pre-configured variants for different sampling focus
LOG_DOMINATE_ANOMALY_CONFIG = AnomalyScoreConfig(
    status_error_weight=3.0,  # Reduced from 5.0
    log_error_weight=5.0,  # Increased from 2.0
    log_warning_weight=3.0,  # Increased from 1.0
    latency_p90_thresholds=[
        (5.0, 1.5),  # Reduced from 3.0
        (3.0, 1.0),  # Reduced from 2.0
        (1.5, 0.5),  # Reduced from 1.0
    ],
)

LATENCY_DOMINATE_ANOMALY_CONFIG = AnomalyScoreConfig(
    status_error_weight=2.0,  # Reduced from 5.0
    log_error_weight=1.0,  # Reduced from 2.0
    log_warning_weight=0.5,  # Reduced from 1.0
    latency_p90_thresholds=[
        (5.0, 6.0),  # Increased from 3.0
        (3.0, 4.0),  # Increased from 2.0
        (1.5, 2.0),  # Increased from 1.0
    ],
)
