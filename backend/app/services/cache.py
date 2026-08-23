import collections
import re
import time
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class ExactL1Cache:
    """
    Synchronous Exact L1 In-Memory Cache.
    
    This cache uses an OrderedDict to maintain Least Recently Used (LRU) eviction.
    It conservatively normalizes queries for exact matching (lowercase, collapsed whitespace).
    It strictly validates that only 'grounded' answers are cached.
    """
    def __init__(self, capacity: int = 500, default_ttl_seconds: int = 600):
        self.capacity = capacity
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: collections.OrderedDict[str, Dict[str, Any]] = collections.OrderedDict()
        
        # Simple internal statistics for future telemetry exposure
        self.hit_count = 0
        self.miss_count = 0

    def _normalize_query(self, query: str) -> str:
        """
        Conservatively normalizes a query.
        - Trims leading/trailing whitespace
        - Collapses consecutive whitespace into a single space
        - Converts to lowercase
        - Preserves punctuation to retain semantic meaning (e.g. question vs statement)
        """
        query = query.strip().lower()
        return re.sub(r'\s+', ' ', query)

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cache entry for the given query if it exists and is not expired.
        Updates LRU recency on a cache hit.
        Returns None on a cache miss or expired entry.
        """
        start_time = time.perf_counter_ns()
        normalized_query = self._normalize_query(query)
        
        if normalized_query not in self.cache:
            self.miss_count += 1
            return None
            
        entry = self.cache[normalized_query]
        
        # Check TTL using monotonic clock
        current_monotonic_time = time.monotonic()
        if current_monotonic_time > entry["expires_at_monotonic"]:
            # Entry has expired; lazily remove it
            del self.cache[normalized_query]
            self.miss_count += 1
            return None
            
        # Update LRU recency: move to the end (most recently used)
        self.cache.move_to_end(normalized_query)
        
        self.hit_count += 1
        
        # Record lookup latency
        end_time = time.perf_counter_ns()
        latency_ms = (end_time - start_time) / 1_000_000.0
        
        # Construct the internal result object (avoiding Pydantic per Phase 1 constraints)
        result = {
            "hit": True,
            "route": "l1_exact",
            "answer_text": entry["answer_text"],
            "evidence_chunk_ids": entry["evidence_chunk_ids"],
            "retrieval_confidence": entry["retrieval_confidence"],
            "grounding_status": entry["grounding_status"],
            "created_at": entry["created_at"],
            "ttl_seconds": entry["ttl_seconds"],
            "latency_ms": latency_ms
        }
        
        return result

    def put(
        self, 
        query: str, 
        answer_text: str, 
        evidence_chunk_ids: list[str], 
        retrieval_confidence: float, 
        grounding_status: str, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Stores an answer in the cache if it is grounded.
        Raises ValueError if the grounding_status is not 'grounded'.
        Enforces LRU capacity constraints.
        """
        # Safe storage boundary check
        if grounding_status != "grounded":
            raise ValueError(f"Refusing to cache unsafe answer. Grounding status: {grounding_status}")
            
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        normalized_query = self._normalize_query(query)
        
        current_monotonic_time = time.monotonic()
        
        entry = {
            "query": normalized_query,
            "answer_text": answer_text,
            "evidence_chunk_ids": evidence_chunk_ids,
            "retrieval_confidence": retrieval_confidence,
            "grounding_status": grounding_status,
            "created_at": datetime.now(timezone.utc),  # Wall-clock metadata for TRD requirements
            "expires_at_monotonic": current_monotonic_time + ttl,
            "ttl_seconds": ttl
        }
        
        # If the key already exists, updating it should make it the most recently used
        if normalized_query in self.cache:
            self.cache[normalized_query] = entry
            self.cache.move_to_end(normalized_query)
        else:
            self.cache[normalized_query] = entry
            
        # LRU capacity enforcement
        if len(self.cache) > self.capacity:
            # popitem(last=False) pops the first item (least recently used)
            self.cache.popitem(last=False)

class SemanticL2Cache:
    """
    Synchronous Semantic L2 In-Memory Cache.
    
    This cache uses an OrderedDict to maintain Least Recently Used (LRU) eviction.
    It evaluates query embeddings using true cosine similarity, handling non-normalized vectors.
    It strictly validates that only 'grounded' answers are cached.
    """
    def __init__(self, capacity: int = 500, default_ttl_seconds: int = 600, semantic_threshold: float = 0.95):
        self.capacity = capacity
        self.default_ttl_seconds = default_ttl_seconds
        self.semantic_threshold = semantic_threshold
        self.cache: collections.OrderedDict[str, Dict[str, Any]] = collections.OrderedDict()
        
        self.hit_count = 0
        self.miss_count = 0
        
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        if len(vec1) != len(vec2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

    def _jaccard_similarity(self, list1: list[str], list2: list[str]) -> float:
        set1, set2 = set(list1), set(list2)
        if not set1 and not set2:
            return 1.0 # Both empty means they match exactly
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    def get(self, query_embedding: list[float]) -> Optional[Dict[str, Any]]:
        start_time = time.perf_counter_ns()
        
        if not query_embedding:
            self.miss_count += 1
            return None
            
        best_match_key = None
        best_score = -1.0
        
        current_monotonic_time = time.monotonic()
        keys_to_delete = []
        
        for key, entry in self.cache.items():
            if current_monotonic_time > entry["expires_at_monotonic"]:
                keys_to_delete.append(key)
                continue
                
            score = self._cosine_similarity(query_embedding, entry["query_embedding"])
            if score >= self.semantic_threshold and score > best_score:
                best_score = score
                best_match_key = key
                
        for key in keys_to_delete:
            del self.cache[key]
            
        if not best_match_key:
            self.miss_count += 1
            return None
            
        entry = self.cache[best_match_key]
        self.cache.move_to_end(best_match_key)
        self.hit_count += 1
        
        end_time = time.perf_counter_ns()
        latency_ms = (end_time - start_time) / 1_000_000.0
        
        result = {
            "hit": True,
            "route": "l2_semantic",
            "answer_text": entry["answer_text"],
            "evidence_chunk_ids": entry["evidence_chunk_ids"],
            "retrieval_confidence": entry["retrieval_confidence"],
            "grounding_status": entry["grounding_status"],
            "created_at": entry["created_at"],
            "ttl_seconds": entry["ttl_seconds"],
            "latency_ms": latency_ms
        }
        
        return result

    def put(
        self, 
        query: str, 
        query_embedding: list[float],
        answer_text: str, 
        evidence_chunk_ids: list[str], 
        retrieval_confidence: float, 
        grounding_status: str, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        if grounding_status != "grounded":
            raise ValueError(f"Refusing to cache unsafe answer. Grounding status: {grounding_status}")
            
        if not query_embedding:
            return
            
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        current_monotonic_time = time.monotonic()
        
        # Near-duplicate write suppression
        for key, existing_entry in self.cache.items():
            jaccard = self._jaccard_similarity(evidence_chunk_ids, existing_entry["evidence_chunk_ids"])
            if jaccard >= 0.95:
                # Update existing rather than duplicate
                existing_entry["query"] = query
                existing_entry["query_embedding"] = query_embedding
                existing_entry["answer_text"] = answer_text
                existing_entry["retrieval_confidence"] = retrieval_confidence
                existing_entry["created_at"] = datetime.now(timezone.utc)
                existing_entry["expires_at_monotonic"] = current_monotonic_time + ttl
                existing_entry["ttl_seconds"] = ttl
                self.cache.move_to_end(key)
                return
                
        entry_key = str(uuid.uuid4())
        
        entry = {
            "query": query,
            "query_embedding": query_embedding,
            "answer_text": answer_text,
            "evidence_chunk_ids": evidence_chunk_ids,
            "retrieval_confidence": retrieval_confidence,
            "grounding_status": grounding_status,
            "created_at": datetime.now(timezone.utc),
            "expires_at_monotonic": current_monotonic_time + ttl,
            "ttl_seconds": ttl
        }
        
        self.cache[entry_key] = entry
        
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
