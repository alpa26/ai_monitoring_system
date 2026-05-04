import numpy as np

def get_severity(score, threshold, history=None):
    if history is not None:
        p95 = np.percentile(history, 95)
        p99 = np.percentile(history, 99)
    else:
        p95 = threshold * 1.5
        p99 = threshold * 2

    if score > p99:
        return "critical"
    elif score > p95:
        return "high"
    elif score > threshold:
        return "medium"
    else:
        return "low"