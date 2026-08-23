import re
import time
from typing import Optional

FALLBACK_MESSAGE = (
    "I could not find enough relevant information in the provided "
    "knowledge base to answer this reliably."
)

class GuardrailService:
    def __init__(self, lexical_threshold: float = 0.3):
        self.lexical_threshold = lexical_threshold

    def _create_result(self, passed: bool, outcome: str, reason: Optional[str], confidence: float, start_time: int) -> dict:
        end_time = time.perf_counter_ns()
        latency_ms = (end_time - start_time) / 1_000_000.0
        return {
            "passed": passed,
            "outcome": outcome,
            "reason": reason,
            "confidence": confidence,
            "latency_ms": latency_ms
        }

    def validate_query(self, query: str) -> dict:
        start_time = time.perf_counter_ns()
        
        query_stripped = query.strip()
        if not query_stripped:
            return self._create_result(False, "abstain", "Empty query", 1.0, start_time)
            
        if len(query_stripped) < 5:
            return self._create_result(False, "abstain", "Query too short", 1.0, start_time)
            
        # Lightweight regex for prompt injection
        query_lower = query_stripped.lower()
        injection_patterns = [
            r"ignore previous instructions",
            r"disregard instructions",
            r"system prompt"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_lower):
                return self._create_result(False, "abstain", "Potential prompt injection detected", 1.0, start_time)
                
        return self._create_result(True, "pass", None, 1.0, start_time)

    def validate_retrieval(self, top_1_score: float, evidence_count: int, threshold: float = 0.3) -> dict:
        start_time = time.perf_counter_ns()
        
        if evidence_count == 0:
            return self._create_result(False, "abstain", "No evidence found", 1.0, start_time)
            
        if top_1_score < threshold:
            return self._create_result(False, "abstain", "Top retrieval score below threshold", top_1_score, start_time)
            
        return self._create_result(True, "pass", None, top_1_score, start_time)

    def validate_grounding(self, answer: str, evidence_texts: list[str]) -> dict:
        start_time = time.perf_counter_ns()
        
        answer_stripped = answer.strip()
        if not answer_stripped:
            return self._create_result(False, "regenerate", "Empty answer", 1.0, start_time)
            
        if not evidence_texts:
            return self._create_result(False, "regenerate", "Empty evidence texts", 1.0, start_time)
            
        combined_evidence = " ".join(evidence_texts)
        
        # Tokenization and lexical overlap
        ans_norm = re.sub(r'[^\w\s]', '', answer_stripped.lower())
        ev_norm = re.sub(r'[^\w\s]', '', combined_evidence.lower())
        
        ans_tokens = set(ans_norm.split())
        ev_tokens = set(ev_norm.split())
        
        if not ans_tokens:
            return self._create_result(False, "regenerate", "Answer contains no valid words", 1.0, start_time)
            
        coverage = len(ans_tokens.intersection(ev_tokens)) / len(ans_tokens)
        if coverage < self.lexical_threshold:
            return self._create_result(False, "regenerate", f"Lexical overlap ({coverage:.2f}) below threshold", coverage, start_time)
            
        # Numeric claim heuristic
        ans_numbers = set(re.findall(r'\b\d+\b', answer_stripped))
        ev_numbers = set(re.findall(r'\b\d+\b', combined_evidence))
        
        unsupported_numbers = ans_numbers - ev_numbers
        if unsupported_numbers:
            return self._create_result(False, "regenerate", f"Unsupported numeric claims detected: {', '.join(unsupported_numbers)}", coverage, start_time)
            
        return self._create_result(True, "pass", None, coverage, start_time)
