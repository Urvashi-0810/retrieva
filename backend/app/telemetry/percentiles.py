import math

def calculate_percentiles(samples: list[float]) -> dict:
    if not samples:
        return {
            "p50": None,
            "p70": None,
            "p100": None,
            "low_confidence": True,
            "sample_count": 0
        }
        
    sorted_samples = sorted(samples)
    n = len(sorted_samples)
    
    p50_idx = math.ceil(0.50 * n) - 1
    p70_idx = math.ceil(0.70 * n) - 1
    
    # Ensure indices are within bounds
    p50_idx = max(0, min(p50_idx, n - 1))
    p70_idx = max(0, min(p70_idx, n - 1))
    
    p50 = sorted_samples[p50_idx]
    p70 = sorted_samples[p70_idx]
    p100 = sorted_samples[-1]
    
    return {
        "p50": float(p50),
        "p70": float(p70),
        "p100": float(p100),
        "low_confidence": n < 30,
        "sample_count": n
    }
