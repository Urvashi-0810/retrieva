def calculate_critical_paths(record: dict) -> dict:
    """
    Computes rag_hot_path_ms and audio_to_first_response_ms from raw telemetry.
    Returns a new dictionary.
    """
    new_record = record.copy()
    
    def get_ms(key: str) -> float:
        val = new_record.get(key)
        return float(val) if val is not None else 0.0

    # embedding_ms + cache_lookup_ms + [retrieval_ms if cache miss] + guardrail_pre_ms + guardrail_post_ms + llm_ttft_ms
    rag_hot_path_ms = 0.0
    rag_hot_path_ms += get_ms("embedding_ms")
    rag_hot_path_ms += get_ms("cache_lookup_ms")
    
    # TRD explicit check: retrieval_ms only counts on cache miss
    cache_status = new_record.get("cache_status", "disabled")
    if cache_status == "miss" or cache_status == "disabled":
        rag_hot_path_ms += get_ms("retrieval_ms")
        
    rag_hot_path_ms += get_ms("guardrail_pre_ms")
    rag_hot_path_ms += get_ms("guardrail_post_ms")
    rag_hot_path_ms += get_ms("llm_ttft_ms")
    
    new_record["rag_hot_path_ms"] = rag_hot_path_ms
    
    # audio_to_first_response_ms = rag_hot_path_ms + vad_ms + stt_ms + transcript_stabilization_ms
    audio_ms = rag_hot_path_ms
    audio_ms += get_ms("vad_ms")
    audio_ms += get_ms("stt_ms")
    audio_ms += get_ms("transcript_stabilization_ms")
    
    new_record["audio_to_first_response_ms"] = audio_ms
    
    return new_record
