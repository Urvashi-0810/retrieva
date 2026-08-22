TEAM\_WORK\_SPLIT.md
--------------------

### 1\. Team Split Overview

PersonRolePrimary ResponsibilityCriticalityMain Deliverable**Person 1**Core System Engineer / Integration OwnerPipeline orchestration, shared contracts, Groq integration, final merge**Highest**Working orchestrator that routes cache-hit/cache-miss, streams Groq answers, integrates all modules**Person 2**RAG & Data EngineerDataset, chunking, embeddings, LanceDB, retrievalHighRetrievalService returning ranked evidence chunks from MSMARCO-XI**Person 3**Voice & Realtime EngineerWebSocket transport, VAD, Sarvam STTHighLive mic → transcript pipeline feeding the orchestrator**Person 4**Reliability & Observability EngineerCache, guardrails, telemetry, benchmarking, analyticsHighSafe cache/guardrail layer + live P50/P70/P100 dashboard data

**Why Person 1 has the highest criticality:** Person 1 is the only role sitting on the single serial dependency chain that every request must pass through (embed → cache-check → \[retrieve\] → guardrail → generate → stream), owns the contracts everyone else codes against, and is the sole merger into main. If Person 1's orchestrator or contracts are wrong or late, no other person's module can be integrated regardless of how complete it is individually. Persons 2–4 can fail partially (degrade to a fallback) without blocking the demo; Person 1 failing blocks the demo entirely.

### 2\. Person 1 — Detailed Responsibilities

**Owns the single most important runtime path: the orchestrator.**

Responsible for implementing:

*   **Pipeline orchestration** — the PipelineOrchestrator coordinating every stage per request, driven by the pipeline state machine (TRD §25).
    
*   **Central request flow** — accepting a stable query (from either the voice path or a text fallback) and driving it through embed → cache → retrieval/guardrail → generation → streaming.
    
*   **Service coordination** — orchestrator depends on typed interfaces for embedding, retrieval, cache, guardrails, and LLM services; it never contains their internal logic.
    
*   **Cache-hit route coordination** — validate the cached result, stream it, record telemetry, skip retrieval/generation entirely.
    
*   **Cache-miss route coordination** — trigger LanceDB retrieval, pass results through retrieval guardrails, abstain if evidence is insufficient, otherwise proceed to generation.
    
*   **Groq integration** — the LLM client itself (reused HTTP client, streaming, timeout/retry policy) since it sits directly on the hot path Person 1 already owns.
    
*   **Prompt construction** — assembling the system prompt + retrieved evidence into the Groq request.
    
*   **Response streaming coordination** — relaying Groq's token stream outward through whatever the orchestrator's caller (Person 3's WebSocket layer) expects, in a stable, documented shape.
    
*   **Shared contracts** — defines and owns all Pydantic schemas (events, pipeline states, retrieval/cache/guardrail/telemetry models) before anyone else starts coding against them.
    
*   **Integration responsibility** — reviewing and merging every PR, resolving conflicts, keeping main always in a working state.
    
*   **Final end-to-end testing** — verifying the complete voice-to-answer and text-to-answer paths work with the existing frontend.
    
*   **Merge responsibility** — sole merger into main; only role permitted to touch main.py.
    

**Person 1 should NOT own** (to keep workload balanced):

*   Dataset processing, chunking, embedding model selection, or LanceDB internals (Person 2).
    
*   WebSocket transport mechanics, VAD, or STT client implementation (Person 3).
    
*   Cache eviction/similarity logic, guardrail heuristics, telemetry aggregation, or the analytics dashboard's data layer (Person 4).
    
*   Frontend work of any kind.
    

Person 1's job is to write the connective tissue and the two services that structurally cannot be split (orchestration state, Groq call) — not to reimplement every service themselves.

### 3\. Person 2 — Detailed Responsibilities

**Owns everything from raw dataset to a returned RetrievalResult.**

*   **MSMARCO-XI dataset analysis** — confirm the passage-ranking structure (short, already retrieval-sized passages; parallel English/Hindi; is\_selected ground truth; near-duplicate passages across rows).
    
*   **Dataset loading** — load via Hugging Face datasets, streamed if large.
    
*   **Dataset structure understanding** — document field layout (query\_id, Eng\_Query, query, passages.English\_passages, passages.Translated\_passages, is\_selected) so chunking/metadata decisions are grounded in actual structure, not assumption.
    
*   **Passage preparation** — flatten to one row per (passage, language), validate non-empty text, dedup exact-hash then near-duplicate (cosine similarity threshold ~0.97).
    
*   **Chunking strategy** — dataset-aware: keep already-short passages intact by default; only sentence-split passages exceeding a max token threshold; light overlap only across splits of the same passage.
    
*   **Chunk evaluation** — compare "intact" vs. "dynamic split" against the dataset's own is\_selected labels; lock the strategy based on measured recall, not assumption.
    
*   **FastEmbed embedding generation** — batch-embed chunks offline; choose a model that handles the bilingual (English/Hindi) content.
    
*   **LanceDB database setup** — table schema, ANN vs. flat search decision (benchmarked, not assumed), single warm table handle opened once.
    
*   **Ingestion pipeline** — reproducible, checkpointed/resumable script; never run at application startup.
    
*   **Indexing** — build the vector index once ingestion completes.
    
*   **Runtime retrieval** — implement the query-time path: query embedding → LanceDB search → score filtering → evidence selection.
    
*   **Top-k retrieval** — return top-N surviving chunks after confidence filtering.
    
*   **Evidence metadata** — attach chunk\_id, doc\_id, score, rank, language, and provenance to every returned chunk.
    

**Offline vs. runtime split:**

*   **Offline (never on hot path):** dataset loading, cleaning/dedup, chunking, batch embedding, LanceDB writes, index building, chunking evaluation, retrieval self-check against is\_selected.
    
*   **Runtime (hot path):** single query embedding, LanceDB search against the pre-built warm table handle, score filtering, evidence assembly. Nothing dataset-sized ever runs per-request.
    

### 4\. Person 3 — Detailed Responsibilities

**Owns the entire mic-to-transcript path plus the WebSocket transport layer.**

*   **WebSocket communication** — the /ws/voice endpoint: accept connections, parse client events, emit server events.
    
*   **Connection lifecycle** — connect, session tracking, reconnect handling (backoff), disconnect cleanup.
    
*   **Audio frame handling** — receive base64 PCM16 chunks, decode, buffer into VAD-sized frames.
    
*   **Audio streaming** — process frames as they arrive rather than waiting for a complete recording; no new WS connection per utterance.
    
*   **Silero VAD** — run backend-side, once-warmed model; frame-level speech/silence classification.
    
*   **Speech start detection** — debounced onset detection (avoid false triggers from transient noise).
    
*   **Speech end detection** — configurable silence-duration threshold to close an utterance.
    
*   **Sarvam STT integration** — send the VAD-bounded segment to Sarvam; treat as batched-segment by default.
    
*   **Transcript events** — emit transcript\_partial/transcript\_final events matching the shared contract.
    
*   **Partial transcripts if supported** — implement partial-stabilization only if Sarvam actually supports true streaming partials; otherwise skip and go straight to final.
    
*   **Final transcript** — hand the stable/final text to Person 1's orchestrator entry point.
    
*   **Errors** — map STT/VAD failures to the shared error event shape; never let a raw exception reach the client.
    
*   **Cancellation/disconnection** — handle cancel\_request and client disconnect mid-stream by cancelling the in-flight orchestrator task cooperatively.
    

**Fallback strategy if Sarvam's real streaming behavior differs from the TRD's assumption:** default to the batched-segment design first (send full VAD-bounded segment, single STT call, no partials) — build and demo this path before attempting any incremental/streaming variant. If true streaming transcription is confirmed available, partials can be layered on top without changing the final-transcript contract Person 1 depends on. If Sarvam integration itself is unreliable close to demo time, fall back further to a **text query** entry point so the rest of the pipeline still demos live.

### 5\. Person 4 — Detailed Responsibilities

**Owns everything that makes the pipeline safe and measurable, without adding LLM calls.**

*   **Exact cache (L1)** — always-on dict lookup on normalized query string; cheap, near-zero cost.
    
*   **Semantic cache (L2) if feasible** — only implement if time allows; must be benchmarked against direct LanceDB search before being trusted as a net win.
    
*   **Cache hit/miss behavior** — return a typed CacheResult; hit path skips retrieval/generation entirely.
    
*   **Safe cache entries** — a cache entry is written only when the corresponding answer was grounded — never cache an ungrounded or abstained answer.
    
*   **Cache validation** — TTL, max-size, LRU eviction, near-duplicate write suppression.
    
*   **Guardrails** — pre-generation: empty/too-short query rejection, prompt-injection heuristic check, retrieval-confidence-based off-topic gating.
    
*   **Grounding validation** — post-generation lexical/embedding overlap check between the answer and retrieved evidence; no second LLM call.
    
*   **Insufficient evidence handling** — abstain (fixed fallback message) rather than let a low-confidence/empty retrieval reach generation.
    
*   **Telemetry collection** — high-resolution (perf\_counter\_ns) per-stage timers; fire-and-forget persistence, never awaited inline.
    
*   **Latency measurement** — per-stage durations plus the derived rag\_hot\_path\_ms and audio\_to\_first\_response\_ms, following the critical-path (non-naive-summation) rule.
    
*   **P50 / P70 / P100** — percentile calculation over collected samples, no silent outlier removal.
    
*   **Cache hit rate** — tracked and exposed for the dashboard.
    
*   **Benchmark execution** — a script that runs a test query set through the live pipeline and reports percentiles per category.
    
*   **Analytics endpoints** — REST/WS endpoints exposing live summary stats to the frontend dashboard.
    

**Priority given 8 hours (highest to lowest):**

1.  L1 exact cache + core guardrails (empty query, off-topic, abstention) — these directly protect demo correctness.
    
2.  Telemetry timers + pipeline\_metrics emission — needed for any dashboard to show real numbers.
    
3.  Percentile calculation + /api/analytics/summary.
    
4.  Semantic (L2) cache — only if L1 + guardrails + telemetry are already solid.
    
5.  Full benchmark script — nice to have; live per-request telemetry can substitute if this doesn't finish.
    

### 6\. Module and File Ownership

Module/FileOwnerPurposeOther Members Allowed to Modify?app/main.pyPerson 1App factory, startup/shutdown, DI wiringNoapp/schemas/\* (events, pipeline states, retrieval, telemetry, errors)Person 1Shared Pydantic contractsNo — request changes via Person 1app/services/interfaces.pyPerson 1Service Protocols the orchestrator depends onNo — request changes via Person 1app/pipeline/orchestrator.pyPerson 1Core request orchestrationNoapp/pipeline/state\_machine.pyPerson 1Pipeline state transitionsNoapp/services/llm.pyPerson 1Groq streaming clientNoapp/core/config.pyPerson 1Environment-driven settingsNoapp/services/embedding.pyPerson 2FastEmbed singletonNoapp/services/retrieval.pyPerson 2LanceDB query implementationNoscripts/analyze\_dataset.pyPerson 2Dataset structure analysisNoscripts/ingest\_dataset.pyPerson 2Offline ingestionNoscripts/evaluate\_chunking.pyPerson 2Chunking strategy evaluationNobackend/data/Person 2Local LanceDB storage (never committed)Noapp/websocket/router.pyPerson 3/ws/voice endpointNoapp/websocket/manager.pyPerson 3Connection lifecycle managementNoapp/services/vad.pyPerson 3Silero VAD wrapperNoapp/services/stt.pyPerson 3Sarvam STT clientNoapp/services/cache.pyPerson 4Exact/semantic cacheNoapp/services/guardrails.pyPerson 4Pre/post-generation checksNoapp/telemetry/collector.pyPerson 4Timing collectionNoapp/telemetry/metrics.pyPerson 4Critical-path aggregationNoapp/telemetry/percentiles.pyPerson 4P50/P70/P100 mathNoapp/api/analytics.pyPerson 4Analytics REST/WS endpointsNoapp/api/benchmark.pyPerson 4Benchmark trigger endpointNoscripts/benchmark.pyPerson 4Benchmark run scriptNo

**Shared contract modules** (all under Person 1's control, changeable only with Person 1's sign-off): app/schemas/\*, app/services/interfaces.py, app/main.py.

### 7\. Shared Contracts

All of these must be frozen by Person 1 **before** parallel implementation begins.

ContractPurposeFields (minimum)ProducerConsumerOwner**Pipeline states**Single source of truth for valid pipeline stages/transitionsEnum of states (IDLE…COMPLETED/ERROR/CANCELLED) + valid-transition mapPerson 1Person 1 (orchestrator), Person 3 (WS layer)Person 1**WebSocket event envelope**Consistent client↔server message shapetype, request\_id, timestamp, dataPerson 1 (shape), Person 3 (emits)Frontend, Person 1Person 1**Transcript event**Carries STT output to the orchestratorrequest\_id, text, is\_final, stabilityPerson 3Person 1Person 1**Retrieval result**Carries LanceDB search outputchunks, latency\_ms, confidence, statusPerson 2Person 1 (orchestrator), Person 4 (guardrails)Person 1**Evidence chunk**One retrieved passage with provenancechunk\_id, document\_id, text, score, rank, metadataPerson 2Person 1, Person 4Person 1**Cache result**Outcome of a cache lookuphit, route, answer, evidence\_chunk\_ids, confidence, latency\_msPerson 4Person 1Person 1**Guardrail result**Outcome of a guardrail checkpassed, outcome, reason, confidence, latency\_msPerson 4Person 1Person 1**Telemetry / pipeline metrics**Per-request stage timingsvad\_ms, stt\_ms, embedding\_ms, cache\_lookup\_ms, retrieval\_ms, guardrail\_\*\_ms, llm\_ttft\_ms, llm\_generation\_ms, derived rag\_hot\_path\_ms/audio\_to\_first\_response\_ms, grounding\_statusPerson 4Person 1, Frontend dashboardPerson 1**Final answer / LLM result event**Carries the completed answer and grounding status downstreamrequest\_id, full\_text, grounding\_status, evidence\_chunk\_ids, ttft\_ms, generation\_msPerson 1Person 3 (relays over WS), FrontendPerson 1**Error event**Consistent error shape across WS and RESTrequest\_id, error\_code, stage, message, recoverableAny service (via Person 1's error mapping)Person 3 (relays), FrontendPerson 1

Person 1 is the controller of every contract above — no one else redefines a field independently, even inside their own module.

### 8\. Dependency Graph

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Person 2 → RetrievalResult contract → Person 1 (orchestrator consumes it)  Person 3 → TranscriptEvent contract → Person 1 (orchestrator entry point)  Person 4 → CacheResult / GuardrailResult / PipelineMetrics contracts → Person 1  Person 1 → owns and freezes all contracts → unblocks Persons 2, 3, 4  Person 1 → Integration → merges 2, 3, 4 into main   `

**What can be developed fully in parallel once contracts are frozen:**

*   Person 2's dataset analysis, chunking, ingestion, and retrieval implementation (only needs to satisfy the RetrievalResult shape — can be tested against a mock query independent of the orchestrator).
    
*   Person 3's VAD/STT implementation and WebSocket transport (only needs to produce a valid TranscriptEvent — can be tested with recorded audio independent of the orchestrator).
    
*   Person 4's cache/guardrail/telemetry implementation (only needs to satisfy CacheResult/GuardrailResult/PipelineMetrics — can be unit-tested against mock RetrievalResult objects, not real LanceDB data).
    
*   Person 1's orchestrator, state machine, and Groq client can all be built against **stub** implementations of the other three services from the very start.
    

**What must be frozen before anyone starts implementing:**

*   All contracts in Section 7.
    
*   The pipeline state machine's valid transitions.
    
*   The WebSocket event type list.
    
*   The service Protocol signatures (EmbeddingServiceProtocol, RetrievalServiceProtocol, CacheServiceProtocol, GuardrailServiceProtocol, LLMServiceProtocol, VADServiceProtocol, STTServiceProtocol, TelemetryCollectorProtocol).
    

### 9\. Implementation Order for 8 Hours

TimeActivityWho**Hour 0–0.5**Person 1 freezes all shared contracts and Protocol interfaces; team reviews togetherAll (led by Person 1)**Hour 0.5–2**Parallel start: Person 1 begins orchestrator + state machine against stubs; Person 2 begins dataset analysis + ingestion script; Person 3 begins WebSocket skeleton + VAD; Person 4 begins cache (L1) + core guardrailsAll, parallel**Hour 2–4**Person 1 implements Groq client and wires it into the orchestrator (still against stubs where needed); Person 2 finishes ingestion, embeds and populates LanceDB, implements real retrieval; Person 3 integrates Sarvam STT, gets a real transcript flowing; Person 4 finishes telemetry timers and percentile calculationAll, parallel**Hour 4–5**First integration pass: Person 1 merges Person 2's retrieval PR; verify a text query returns real evidence and a grounded answerPerson 1 + Person 2**Hour 5–6**Second integration pass: Person 1 merges Person 4's cache/guardrail/telemetry PR; verify abstention on a known-unanswerable query and cache-hit shortcut on a repeated queryPerson 1 + Person 4**Hour 6–7**Third integration pass: Person 1 merges Person 3's voice/WebSocket PR; verify full mic-to-answer path against the existing frontendPerson 1 + Person 3**Hour 7–8**Buffer: fix integration bugs, confirm fallback paths, final demo run-throughAll

No one waits on another person's _complete_ implementation — each merges as soon as their contract is satisfied, and Person 1 integrates continuously rather than batching all merges at hour 7.

### 10\. Git Branch Strategy

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   main  ├── person1/core-pipeline  ├── person2/rag-data  ├── person3/voice-websocket  └── person4/reliability-telemetry   `

*   **Branch creation:** each person creates their own branch off main at hour 0, immediately after contracts are frozen.
    
*   **Pushing:** each person pushes only to their own branch; no one pushes to another person's branch without asking.
    
*   **Opening PRs:** each person opens a PR against main when their module satisfies its shared contract and passes its own independent acceptance test (Section 13).
    
*   **Reviewing:** Person 1 reviews every PR — checking contract compliance and that the smoke/integration test still passes.
    
*   **Merging:** Person 1 is the sole merger into main. No direct pushes to main by anyone else, at any point.
    

### 11\. Merge Strategy

**Safest merge order, based on actual dependencies:**

1.  **Person 1's foundation** — contracts, state machine, orchestrator skeleton, stub services — is the baseline main starts from.
    
2.  **Merge Person 2 next.**
    
    *   Must already work: retrieval returns a real, non-empty RetrievalResult for at least one known-answerable query.
        
    *   Person 1 verifies: a manual query through the orchestrator (still with stub cache/guardrails) reaches real evidence.
        
    *   Could break: nothing else depends on Person 2, so this merge is low-risk.
        
    *   Tests to run: retrieval-only smoke test, then full text-query smoke test.
        
3.  **Merge Person 4 next.**
    
    *   Must already work: cache lookup returns a typed CacheResult; guardrails correctly abstain on an off-topic/low-confidence query.
        
    *   Person 1 verifies: a known-unanswerable query now abstains instead of hallucinating; a repeated query hits cache and skips retrieval.
        
    *   Could break: guardrail thresholds might be too strict/loose against Person 2's real retrieval confidence distribution — recalibrate together if needed.
        
    *   Tests to run: cache-hit/miss test, abstention test, full text-query smoke test again.
        
4.  **Merge Person 3 last.**
    
    *   Must already work: a recorded/live audio segment produces a valid TranscriptEvent reaching the orchestrator.
        
    *   Person 1 verifies: full mic-to-answer path completes end-to-end against the existing frontend.
        
    *   Could break: WebSocket event shapes might drift from what the frontend's demo mode expects — check against frontend's existing event listeners before merging.
        
    *   Tests to run: full end-to-end voice smoke test, plus a repeat of the text-query test to confirm nothing regressed.
        

**Avoiding a big-bang merge at the end:** each PR merges as soon as its own acceptance test passes (Section 13), spread across hours 4–7 rather than saved for hour 8 — by the time Person 3's PR lands, Persons 2 and 4's work is already proven stable in main.

### 12\. Merge Conflict Prevention Rules

*   Never edit a file outside your ownership row in Section 6.
    
*   Do not casually change any shared contract (app/schemas/\*, app/services/interfaces.py) — route changes through Person 1.
    
*   Do not rename shared modules or files without discussing with the whole team first.
    
*   Do not reformat or "clean up" files you don't own, even in passing.
    
*   Do not commit generated dataset artifacts, LanceDB database files, or any data/ output.
    
*   Do not commit .env files or hardcode API keys anywhere.
    
*   Keep PRs focused on your owned module only — no drive-by edits to other files.
    
*   Sync your branch with main only right before opening a PR, not continuously — avoids noisy, conflict-prone rebases mid-work.
    
*   Person 1 is the sole authority on integration-affecting changes (main.py, contracts, orchestrator).
    
*   If you believe a contract needs to change mid-implementation, flag it to Person 1 immediately rather than working around it locally — silent workarounds are what cause late-stage integration failures.
    
*   Prefer additive changes to shared contracts (new optional fields) over breaking ones during the 8-hour window.
    

### 13\. Individual Acceptance Tests

**Person 1:** A query (text, bypassing voice) enters the orchestrator and correctly routes through either the cache-hit path (returns a cached answer, skips retrieval) or the cache-miss path (retrieves, guards, generates, streams) depending on cache state, ending in a COMPLETED state with a non-empty answer.

**Person 2:** A query embedding, run against the populated LanceDB table, returns a ranked list of evidence chunks with scores and provenance for a known-answerable dataset query, and returns an empty/low-confidence result for a known "No Answer Present" query.

**Person 3:** A recorded audio segment fed through VAD correctly triggers speech-start/speech-end, the resulting segment is sent to Sarvam STT, and a transcript\_final event with the correct text is produced.

**Person 4:** (a) A repeated query hits the exact cache and returns without touching retrieval. (b) A RetrievalResult with confidence below threshold correctly produces an abstain guardrail outcome. (c) A synthetic array of latency samples produces correct P50/P70/P100 values.

### 14\. Integration Acceptance Test

**Full flow:**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Frontend → WebSocket → Audio → VAD → STT → Transcript  → Embedding → Cache → LanceDB (if needed) → Guardrails  → Groq → Streaming answer → Telemetry → Frontend analytics   `

**Scenarios to verify:**

*   **Cache-hit scenario:** a query matching a prior grounded answer returns the cached answer immediately, with cache\_route reflected in telemetry, and retrieval/generation stages skipped.
    
*   **Cache-miss scenario:** a novel, answerable query flows through retrieval → guardrail → Groq → streamed answer, with grounding\_status: grounded, and the answer is written to cache afterward.
    
*   **Insufficient-evidence scenario:** a known off-topic or "No Answer Present" query is correctly abstained, returning the fixed fallback message, with grounding\_status: abstained — never a hallucinated answer.
    
*   **Text fallback scenario:** with voice intentionally bypassed, a text query submitted directly reaches the same orchestrator and produces an equivalent result to the voice path, confirming the fallback works if voice is unreliable on demo day.
    

### 15\. Fallback Priorities

**P0 — Must work for the demo:**

*   Text query path through the orchestrator (fallback if voice fails).
    
*   Core RAG: real retrieval against the ingested MSMARCO-XI data.
    
*   Groq-generated, grounded answers with streaming.
    
*   Basic WebSocket connection + connection\_ready/answer\_delta/answer\_complete events.
    
*   Final-transcript STT path (no partials required).
    
*   L1 exact cache.
    
*   Core guardrails: empty-query rejection, off-topic/low-confidence abstention, post-generation grounding check.
    
*   Basic telemetry: per-stage timers populated on pipeline\_metrics events.
    

**P1 — Important if time allows:**

*   Semantic (L2) cache.
    
*   Partial-transcript stabilization for a more responsive voice UX.
    
*   Full percentile-based analytics dashboard wired to live data.
    
*   Prompt-injection heuristic guardrail.
    

**P2 — Nice to have:**

*   scripts/benchmark.py fully automated benchmark runs.
    
*   ANN indexing tuning / flat-vs-ANN comparison in LanceDB.
    
*   Reranking experiments.
    
*   Near-duplicate cache-write suppression.
    

### 16\. Hackathon Demo Ownership

*   **Person 1** explains the core architecture: how a query is orchestrated end-to-end, the pipeline state machine, the cache-hit vs. cache-miss decision, and how the four modules integrate into one system.
    
*   **Person 2** explains the RAG side: how MSMARCO-XI was analyzed and chunked, why the chunking strategy was chosen (dataset-aware, mostly-intact passages), and how retrieval quality was validated against is\_selected ground truth.
    
*   **Person 3** explains the voice/real-time side: how audio flows from the browser through VAD and Sarvam STT into a stable transcript, and how the system handles interruptions/cancellation.
    
*   **Person 4** explains reliability and observability: how the cache avoids serving stale/wrong answers, how guardrails prevent hallucination on off-topic or unanswerable queries, and what the live P50/P70/P100 telemetry shows about system performance.