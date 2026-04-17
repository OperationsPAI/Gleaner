#!/usr/bin/env -S uv run -s


from rcabench_platform.v2.cli.main import main
from rcabench_platform.v2.samplers.spec import global_sampler_registry

from gleaner import (
    AnomalyPureDiversityVariant,
    GleanerSampler,
    LatencyDominateVariant,
    LogDominateVariant,
    NoAnomalyDetectionVariant,
    NoDPPVariant,
    NoLogsNoADVariant,
    NoLogsVariant,
    NoRebalanceVariant,
    PureDiversityVariant,
    TopScoreVariant,
    WLKernelVariant,
)

if __name__ == "__main__":
    registry = global_sampler_registry()

    registry["gleaner"] = GleanerSampler
    registry["gleaner_no_logs"] = NoLogsVariant
    registry["gleaner_no_ad"] = NoAnomalyDetectionVariant
    registry["gleaner_no_logs_no_ad"] = NoLogsNoADVariant
    registry["gleaner_pure_diversity"] = PureDiversityVariant
    registry["gleaner_wl_kernel"] = WLKernelVariant
    registry["gleaner_no_dpp"] = NoDPPVariant
    registry["gleaner_top_score"] = TopScoreVariant
    registry["gleaner_log_dominate"] = LogDominateVariant
    registry["gleaner_latency_dominate"] = LatencyDominateVariant
    registry["gleaner_no_rebalance"] = NoRebalanceVariant
    registry["gleaner_anomaly_pure_diversity"] = AnomalyPureDiversityVariant
    main(enable_builtin_algorithms=False)
 