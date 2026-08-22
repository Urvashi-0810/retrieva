Product Requirements Document (PRD)
===================================

1\. Document Overview
---------------------

**Product Name:** TBD**Project Type:** Voice-Enabled Retrieval-Augmented Generation System**Primary Challenge:** HH Goa 2026 — Task 2**Core Goal:** Build a production-inspired, ultra-low-latency voice-enabled RAG pipeline that accepts spoken user queries, retrieves grounded information from the provided AI4Bharat MSMARCO-XI dataset, applies guardrails and structured orchestration, and returns a reliable answer with measurable latency analytics.

2\. Problem Statement
=====================

Traditional RAG applications are often designed as sequential pipelines:

> User speaks → Audio uploaded → Speech-to-text completes → Database search → LLM processing → Final response

This approach introduces unnecessary waiting time, especially for voice-based interfaces where perceived responsiveness is critical.

The system should therefore solve the following problems:

*   Voice transcription latency.
    
*   Background noise processing.
    
*   Repeated queries causing unnecessary retrieval and inference.
    
*   Slow network-based vector database access.
    
*   Weak or naive document chunking.
    
*   LLM hallucinations.
    
*   Answers not grounded in retrieved evidence.
    
*   Off-topic queries.
    
*   Unsafe or inappropriate inputs.
    
*   Lack of visibility into latency across the RAG pipeline.
    
*   Lack of structured orchestration, retries, and failure handling.
    

The product will implement an optimized architecture that prioritizes:

1.  Low latency.
    
2.  Streaming interaction.
    
3.  Advanced chunking and retrieval.
    
4.  Semantic caching.
    
5.  Grounded answers.
    
6.  Guardrail validation.
    
7.  Measurable system performance.
    

3\. Product Vision
==================

Create a voice-first RAG system where a user can ask a question naturally and receive a grounded answer with near-instant feedback.

The system should demonstrate that high-quality RAG does not require sacrificing speed.

The final experience should feel like:

> Speak → See live transcription → System retrieves evidence → Answer starts streaming immediately → View exactly how fast every stage performed.

The product should also provide a transparent analytics layer showing:

*   Retrieval latency.
    
*   Embedding latency.
    
*   Cache performance.
    
*   Guardrail latency.
    
*   Generation latency.
    
*   End-to-end latency.
    
*   P50 latency.
    
*   P70 latency.
    
*   P100 latency.
    
*   Retrieval quality.
    
*   Grounding status.
    

4\. Target Users
================

4.1 Primary User
----------------

A user who wants to ask questions through voice and receive a fast answer based on a knowledge dataset.

4.2 Technical Evaluators
------------------------

Hackathon judges and technical reviewers evaluating:

*   RAG architecture.
    
*   Latency optimization.
    
*   Chunking strategy.
    
*   Retrieval quality.
    
*   Guardrails.
    
*   Structured orchestration.
    
*   Performance analytics.
    
*   End-to-end functionality.
    

4.3 Development Team
--------------------

Developers and project maintainers who need observability into every stage of the pipeline.

5\. Product Goals
=================

Primary Goals
-------------

### G1. Voice-First Interaction

Allow users to ask questions using microphone input.

### G2. Real-Time Speech Recognition

Convert spoken audio into text using Sarvam AI.

### G3. Advanced Chunking

Implement a multi-strategy chunking pipeline rather than a single naive fixed-size chunking method.

### G4. Fast Retrieval

Retrieve relevant information from the AI4Bharat MSMARCO-XI dataset using LanceDB.

### G5. Semantic Caching

Avoid repeated retrieval and LLM inference for semantically similar queries.

### G6. Grounded Answer Generation

Generate answers based primarily on retrieved evidence.

### G7. Guardrail Protection

Detect and handle:

*   Off-topic queries.
    
*   Unsafe or inappropriate inputs.
    
*   Insufficient context.
    
*   Ungrounded answers.
    
*   Retrieval failures.
    

### G8. Streaming Output

Return the generated answer to the frontend as it is produced.

### G9. Latency Transparency

Expose pipeline performance through a detailed analytics dashboard.

### G10. Benchmarking

Measure latency across a reasonable number of queries and calculate:

*   P50.
    
*   P70.
    
*   P100.
    

6\. Non-Goals
=============

The first version will not focus on:

*   User authentication.
    
*   Long-term user memory.
    
*   Multi-user conversation history.
    
*   Fine-tuning an LLM.
    
*   Training a custom speech recognition model.
    
*   Replacing the provided dataset with an external knowledge base.
    
*   Full enterprise-scale distributed infrastructure.
    

The priority is to build and demonstrate a high-performance RAG pipeline.

7\. Core User Journey
=====================

Step 1: User Opens the Application
----------------------------------

The user sees:

*   Microphone control.
    
*   Live transcript area.
    
*   Generated answer area.
    
*   System status.
    
*   Analytics dashboard.
    

Step 2: User Starts Speaking
----------------------------

The user taps the microphone button.

The frontend:

1.  Requests microphone access.
    
2.  Captures audio.
    
3.  Converts audio into the required streaming format.
    
4.  Sends audio chunks through a persistent WebSocket connection.
    

Step 3: Voice Activity Detection
--------------------------------

Incoming audio is processed by Silero VAD.

The VAD determines whether the incoming audio contains:

*   Speech.
    
*   Silence.
    
*   Background noise.
    

Only relevant speech segments proceed to the speech-to-text pipeline.

This reduces unnecessary downstream processing.

Step 4: Live Transcription
--------------------------

Speech segments are sent to Sarvam AI STT.

The frontend receives:

*   Partial transcripts.
    
*   Updated transcript states.
    
*   Final transcript.
    

The user should be able to see transcription progress in real time.

Step 5: Query Processing Begins
-------------------------------

Once a sufficiently stable or final query is available, the backend:

1.  Normalizes the query.
    
2.  Creates an embedding.
    
3.  Performs semantic cache lookup.
    

Step 6: Semantic Cache Decision
-------------------------------

### Cache Hit

If a semantically similar query has been processed recently:

*   The answer is retrieved from memory.
    
*   LanceDB retrieval is skipped.
    
*   LLM inference is skipped where appropriate.
    
*   The cached answer is returned immediately.
    

### Cache Miss

If no suitable semantic cache match exists:

*   The system proceeds to the retrieval pipeline.
    

Step 7: LanceDB Retrieval
-------------------------

The query embedding is searched against the indexed MSMARCO-XI dataset.

The system retrieves:

*   Top relevant passages.
    
*   Associated metadata.
    
*   Retrieval scores.
    
*   Chunk identifiers.
    

Step 8: Guardrail and Retrieval Validation
------------------------------------------

Before generation, the retrieved evidence is evaluated.

The system checks:

*   Is the query relevant to the dataset?
    
*   Is retrieved context sufficiently relevant?
    
*   Is retrieval confidence above threshold?
    
*   Is the request safe?
    
*   Is there enough evidence to answer?
    

If validation fails, the system should return a controlled fallback response rather than hallucinating.

Step 9: Structured Generation
-----------------------------

Validated context is assembled into a structured prompt.

The harness should manage:

*   Input validation.
    
*   Context formatting.
    
*   Prompt construction.
    
*   LLM invocation.
    
*   Retry logic.
    
*   Timeout handling.
    
*   Error handling.
    
*   Structured output.
    
*   Grounding validation.
    

Step 10: Streaming Answer
-------------------------

Groq Llama-3.1-8B-Instant generates the response.

Tokens are streamed through FastAPI to the frontend.

The frontend progressively renders the answer.

Step 11: Post-Generation Validation
-----------------------------------

The generated answer is evaluated against retrieved context.

Possible outcomes:

### Grounded

The answer is shown to the user.

### Insufficiently Grounded

The system:

*   Regenerates when appropriate.
    
*   Returns a constrained response.
    
*   States that the provided context does not contain enough information.
    

Step 12: Analytics Recording
----------------------------

Every request generates timing data for the pipeline.

The system records:

*   VAD timing.
    
*   STT timing.
    
*   Embedding timing.
    
*   Cache lookup timing.
    
*   Retrieval timing.
    
*   Guardrail timing.
    
*   LLM TTFT.
    
*   Token generation timing.
    
*   Total RAG pipeline latency.
    
*   Total user-visible request latency.
    

8\. Functional Requirements
===========================

FR-1: Voice Input
-----------------

The system shall allow users to initiate voice input from the frontend.

### Requirements

*   Microphone button.
    
*   Start/stop recording state.
    
*   Microphone permission handling.
    
*   Audio capture.
    
*   Audio chunk streaming.
    
*   Connection status indicator.
    

FR-2: Persistent WebSocket
--------------------------

The frontend and FastAPI backend shall maintain a persistent WebSocket connection for voice interaction.

### Requirements

*   Connection establishment.
    
*   Audio streaming.
    
*   Transcript events.
    
*   Status events.
    
*   Partial answer streaming.
    
*   Final answer events.
    
*   Error events.
    
*   Reconnection handling.
    

FR-3: Voice Activity Detection
------------------------------

The backend shall use Silero VAD to detect speech activity.

### Requirements

*   Reject prolonged silence.
    
*   Avoid unnecessary STT processing.
    
*   Detect speech boundaries.
    
*   Support streaming audio.
    
*   Record VAD latency.
    

FR-4: Speech-to-Text
--------------------

The system shall use Sarvam AI as the selected speech-to-text provider.

### Requirements

*   Real-time transcription.
    
*   Partial transcript support where available.
    
*   Final transcript generation.
    
*   Error handling.
    
*   STT latency measurement.
    

FR-5: Dataset Processing
------------------------

The system shall use the provided AI4Bharat MSMARCO-XI dataset as the knowledge source.

The dataset shall be processed before runtime and stored in a retrieval-ready form.

9\. Advanced Chunking Strategy
==============================

The chunking implementation is a major evaluation area.

The system shall not rely exclusively on one naive fixed-size chunking approach.

Instead, the indexing pipeline shall support multiple chunking strategies.

9.1 Strategy A: Sentence-Aware Chunking
---------------------------------------

Documents are split according to sentence boundaries.

Benefits:

*   Better semantic coherence.
    
*   Fewer broken sentences.
    
*   Cleaner retrieval units.
    

9.2 Strategy B: Semantic Chunking
---------------------------------

The system identifies semantic boundaries between sections or sentences.

Conceptually:

1.  Generate embeddings for adjacent sentence groups.
    
2.  Measure semantic similarity.
    
3.  Detect significant topic shifts.
    
4.  Create chunk boundaries at topic transitions.
    

This avoids splitting unrelated information into the same chunk.

9.3 Strategy C: Dynamic Chunk Sizing
------------------------------------

Chunk size should depend on content structure rather than using a single fixed token count.

The system may use:

*   Minimum chunk size.
    
*   Maximum chunk size.
    
*   Semantic breakpoints.
    
*   Sentence boundaries.
    
*   Content density.
    

9.4 Strategy D: Overlap Handling
--------------------------------

Where appropriate, adjacent chunks shall include controlled overlap.

This helps preserve context across chunk boundaries.

Overlap must be measured and optimized to avoid:

*   Excessive duplication.
    
*   Larger index size.
    
*   Retrieval noise.
    

9.5 Strategy E: Metadata-Aware Chunks
-------------------------------------

Each indexed chunk should preserve metadata such as:

*   Document ID.
    
*   Chunk ID.
    
*   Original text.
    
*   Chunking strategy.
    
*   Parent document reference.
    
*   Position.
    
*   Source metadata.
    
*   Embedding version.
    

9.6 Chunking Experimentation
----------------------------

The system should support evaluation of different strategies.

Example comparison:

StrategyRetrieval QualityLatencyIndex SizeFixed-sizeBaselineBaselineLowSentence-awareImprovedLowMediumSemanticHigher qualityMediumMediumHybrid/dynamicTarget approachOptimizedControlled

The final strategy should be selected using actual measured trade-offs.

10\. Semantic Cache Requirements
================================

The system shall include an in-memory semantic cache.

Cache Workflow
--------------

1.  Generate query embedding.
    
2.  Compare with cached query embeddings.
    
3.  Calculate similarity.
    
4.  Check similarity threshold.
    
5.  Return cached answer if similarity is sufficient.
    

Cache Entry
-----------

Each cache entry may contain:

*   Original query.
    
*   Query embedding.
    
*   Answer.
    
*   Retrieved context reference.
    
*   Timestamp.
    
*   Expiration time.
    
*   Grounding status.
    

Cache States
------------

### Hit

A sufficiently similar query is found.

### Miss

No sufficiently similar query exists.

### Expired

A matching entry exists but is no longer valid.

11\. Retrieval Requirements
===========================

FR-6: LanceDB Vector Search
---------------------------

The system shall use LanceDB as the primary vector store.

### Requirements

*   Embedded deployment.
    
*   Local storage.
    
*   Vector similarity search.
    
*   Metadata storage.
    
*   Top-K retrieval.
    
*   Retrieval score measurement.
    
*   Search latency measurement.
    

FR-7: Query Embeddings
----------------------

The system shall generate embeddings using fastembed.

### Requirements

*   Local embedding inference.
    
*   ONNX-based inference.
    
*   Reusable embedding model.
    
*   Consistent embedding space between indexing and query time.
    

FR-8: Retrieval Confidence
--------------------------

The system shall calculate retrieval confidence.

If retrieved results are below the configured relevance threshold, the system should not confidently generate an unsupported answer.

12\. Model Harness Requirements
===============================

The system must implement structured orchestration around model inference.

The harness shall provide:

Input Validation
----------------

Validate:

*   Query exists.
    
*   Query is non-empty.
    
*   Query length is acceptable.
    
*   Audio transcription completed successfully.
    

Retrieval Orchestration
-----------------------

Manage:

*   Cache lookup.
    
*   Retrieval execution.
    
*   Retrieval failure.
    
*   Insufficient context.
    

LLM Invocation
--------------

Manage:

*   Prompt construction.
    
*   API call.
    
*   Timeout.
    
*   Retry policy.
    
*   Streaming response.
    

Structured Output
-----------------

The system should maintain structured internal states such as:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   REQUEST_RECEIVED  → TRANSCRIBING  → QUERY_READY  → CACHE_CHECK  → CACHE_HIT / CACHE_MISS  → RETRIEVING  → RETRIEVAL_VALIDATED  → GENERATING  → STREAMING  → GROUNDED  → COMPLETED   `

Error Recovery
--------------

Handle:

*   WebSocket disconnection.
    
*   STT provider failure.
    
*   Embedding failure.
    
*   LanceDB failure.
    
*   Groq timeout.
    
*   Empty retrieval.
    
*   Guardrail failure.
    

13\. Guardrail Requirements
===========================

The product shall implement guardrails before and after generation.

Pre-Generation Guardrails
-------------------------

### Off-Topic Detection

Determine whether the query is sufficiently related to the available dataset.

### Retrieval Relevance

Determine whether retrieved passages are relevant to the query.

### Unsafe Input Handling

Detect inappropriate or unsupported requests according to configured safety policies.

### Insufficient Evidence

Prevent generation when the retrieved context is too weak.

Post-Generation Guardrails
--------------------------

### Grounding Check

Determine whether the answer is supported by retrieved context.

### Faithfulness Check

Identify unsupported claims.

### Context Alignment

Ensure generated output does not substantially contradict retrieved evidence.

Guardrail Outcomes
------------------

### PASS

Answer is streamed or returned.

### REGENERATE

A new constrained generation attempt may be performed.

### REFUSE / ABSTAIN

The system responds with a safe fallback.

Example:

> I could not find enough relevant information in the provided knowledge base to answer this reliably.

14\. LLM Requirements
=====================

Selected Provider
-----------------

Groq API.

Model
-----

Llama-3.1-8B-Instant, subject to final availability and project testing.

Requirements
------------

*   Streaming generation.
    
*   Low TTFT.
    
*   Timeout handling.
    
*   Structured prompts.
    
*   Grounding instructions.
    
*   Context-aware generation.
    

15\. Response Streaming Requirements
====================================

The backend shall stream answer events to the frontend.

Possible events:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   answer_start  answer_delta  answer_complete  answer_error   `

The frontend should display:

1.  Processing state.
    
2.  Answer generation start.
    
3.  Incremental answer content.
    
4.  Final completion.
    

16\. Latency Requirements
=========================

The system has two important latency perspectives.

16.1 Full User Interaction Latency
----------------------------------

This includes:

*   Speech activity detection.
    
*   STT.
    
*   Query preparation.
    
*   Cache/retrieval.
    
*   Guardrails.
    
*   LLM first token.
    

This represents the complete user experience.

16.2 RAG Decision Window
------------------------

This measures the optimized RAG path beginning when usable transcript text is available.

Example:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Transcript Ready  → Embedding  → Semantic Cache  → LanceDB Retrieval  → Guardrails  → Groq TTFT  → First Response   `

The analytics dashboard should clearly distinguish:

*   STT latency.
    
*   RAG pipeline latency.
    
*   Total end-to-end user latency.
    

This prevents ambiguity in benchmark reporting.

17\. Latency Target
===================

The product should target:

> **Under 200ms for the optimized measured pipeline window where technically applicable and benchmarked under the project test methodology.**

The team must report actual measured results rather than claiming theoretical numbers.

The system should measure:

*   Minimum.
    
*   Maximum.
    
*   Mean.
    
*   Median.
    
*   P50.
    
*   P70.
    
*   P100.
    

18\. Analytics Dashboard
========================

The system shall provide a technical observability dashboard.

18.1 Main Latency Cards
-----------------------

The dashboard shall prominently display:

### P50

Median pipeline latency.

### P70

70th percentile pipeline latency.

### P100

Worst observed measured latency.

18.2 Current Stage Timing Panel
-------------------------------

Display timing for stages such as:

*   Guardrails.
    
*   Embedding.
    
*   Dense search.
    
*   Lexical search if hybrid retrieval is used.
    
*   Reranking.
    
*   Evidence selection.
    
*   Extraction.
    
*   Retrieval-to-answer.
    

The implementation should only show stages actually used by the final pipeline.

18.3 Live SLA Panel
-------------------

Display:

*   P50.
    
*   P70.
    
*   P100.
    
*   SLA status.
    
*   Cache configuration.
    
*   Benchmark information.
    

Example:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   P50: 11.1 ms  P70: 12.8 ms  P100: 21.2 ms  P100 Goal: 50 ms  Status: PASS   `

These values are example dashboard values and must eventually be replaced with real benchmark measurements.

18.4 Retrieval Analysis
-----------------------

For each request, display:

*   Retrieval route.
    
*   Cache status.
    
*   Number of chunks retrieved.
    
*   Number of evidence references.
    
*   Retrieval confidence.
    
*   Grounding result.
    

Example:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Route: Semantic Cache → LanceDB  Evidence: 5 chunks  Confidence: 96%  Grounding: Passed   `

19\. Analytics Data Model
=========================

Each benchmark request should generate structured telemetry.

Example:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "request_id": "uuid",    "timestamp": "ISO-8601",    "query": "user query",    "cache_status": "hit",    "vad_ms": 10.2,    "stt_ms": 48.4,    "embedding_ms": 4.1,    "cache_lookup_ms": 0.7,    "retrieval_ms": 3.9,    "guardrail_ms": 8.3,    "llm_ttft_ms": 72.6,    "rag_pipeline_ms": 89.6,    "total_latency_ms": 138.0,    "grounding_status": "passed"  }   `

20\. Benchmarking Requirements
==============================

The benchmark must use a reasonable number of queries.

A single best-case measurement is not acceptable.

Benchmark Dataset
-----------------

The team should prepare a representative test suite containing:

*   Short queries.
    
*   Long queries.
    
*   Simple factual queries.
    
*   Semantically similar repeated queries.
    
*   Cache-hit queries.
    
*   Cache-miss queries.
    
*   Off-topic queries.
    
*   Low-confidence retrieval queries.
    

Required Statistics
-------------------

The benchmark shall calculate:

### P50

50% of requests complete below this value.

### P70

70% of requests complete below this value.

### P100

The maximum observed latency.

Benchmark Categories
--------------------

Results should ideally distinguish:

CategoryPurposeCache HitMeasures warm semantic cache performanceCache MissMeasures full retrieval pipelineRetrieval OnlyMeasures LanceDB performanceGuardrailMeasures validation overheadGenerationMeasures LLM TTFTEnd-to-EndMeasures complete user-visible pipeline

21\. Frontend Requirements
==========================

The frontend shall provide a professional technical interface.

Required Sections
-----------------

### Voice Interface

*   Microphone button.
    
*   Listening state.
    
*   Audio activity state.
    

### Transcript Panel

*   Partial transcript.
    
*   Final transcript.
    
*   Processing status.
    

### Answer Panel

*   Streaming answer.
    
*   Final answer.
    
*   Grounding status.
    

### Analytics Panel

*   P50.
    
*   P70.
    
*   P100.
    
*   Stage latency breakdown.
    
*   Cache status.
    
*   Retrieval confidence.
    

### Retrieval Analysis

*   Route used.
    
*   Evidence count.
    
*   Confidence.
    
*   Grounding status.
    

22\. Backend Requirements
=========================

The backend shall be implemented using FastAPI.

Core Components
---------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   FastAPI Application  │  ├── WebSocket Manager  │  ├── Audio Processing Service  │   └── Silero VAD  │  ├── STT Service  │   └── Sarvam AI  │  ├── Query Processing Service  │  ├── Embedding Service  │   └── fastembed  │  ├── Semantic Cache  │  ├── Retrieval Service  │   └── LanceDB  │  ├── Guardrail Service  │  ├── Model Harness  │  ├── Groq LLM Service  │  └── Analytics Service   `

23\. Technology Stack
=====================

LayerTechnologyFrontendReactBackendFastAPIReal-Time CommunicationWebSocketAudio ProcessingSilero VADSpeech-to-TextSarvam AIDatasetAI4Bharat MSMARCO-XIChunkingChonkieEmbeddingsfastembedVector DatabaseLanceDBSemantic CacheIn-Memory Vector Similarity CacheGuardrailsCustom Cosine Similarity + PydanticLLMGroqModelLlama-3.1-8B-InstantAnalyticsCustom Latency Telemetry

24\. System Architecture
========================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML                        `USER                           │                           ▼                  [ Microphone Input ]                           │                           ▼                WebSocket Audio Streaming                           │                           ▼                      [ FastAPI ]                           │                           ▼                     [ Silero VAD ]                           │                    Speech Detected                           │                           ▼                    [ Sarvam STT ]                           │                      Live Transcript                           │                           ▼                    [ fastembed ]                           │                           ▼                 [ Semantic Cache ]                    │           │                  HIT          MISS                    │           │                    ▼           ▼               Cached      [ LanceDB ]               Answer           │                    │           ▼                    │     Retrieved Chunks                    │           │                    └──────┬────┘                           │                           ▼                   [ Guardrail Layer ]                           │                   Valid Context?                      │       │                     YES      NO                      │       │                      ▼       ▼                  [ Groq ]  Abstain                      │                      ▼              Streaming Response                      │                      ▼                  [ Frontend ]                           │                           ▼                [ Analytics Collector ]                           │                           ▼            P50 / P70 / P100 Dashboard`

25\. Success Metrics
====================

The project will be considered successful when:

Functional
----------

*   Voice input works.
    
*   Speech is transcribed.
    
*   Relevant dataset context is retrieved.
    
*   Answers are generated.
    
*   Responses stream to the frontend.
    

Retrieval
---------

*   Advanced chunking is implemented.
    
*   Chunking is demonstrably not a single naive fixed-size approach.
    
*   Retrieval uses LanceDB.
    
*   Semantic caching works.
    

Guardrails
----------

*   Off-topic handling works.
    
*   Insufficient evidence handling works.
    
*   Ungrounded answers are constrained.
    

Performance
-----------

*   Stage-level latency is measured.
    
*   P50 is calculated.
    
*   P70 is calculated.
    
*   P100 is calculated.
    
*   Measurements use multiple test queries.
    
*   Actual results are shown in the dashboard.
    

Engineering
-----------

*   Structured model harness exists.
    
*   Retry and failure handling exist.
    
*   Input/output states are structured.
    
*   The live application is deployed.
    

26\. Acceptance Criteria
========================

The project must satisfy the following acceptance criteria:

*   User can ask a question through voice.
    
*   Audio is streamed to the backend.
    
*   Voice activity detection processes audio.
    
*   Sarvam AI performs speech-to-text.
    
*   The provided dataset is indexed.
    
*   Multiple chunking strategies are evaluated or supported.
    
*   A final optimized chunking strategy is implemented.
    
*   fastembed generates embeddings.
    
*   Semantic cache performs similarity lookup.
    
*   Cache hits bypass unnecessary downstream processing.
    
*   LanceDB retrieves relevant passages.
    
*   Guardrails evaluate the request and context.
    
*   The model pipeline is managed through a structured harness.
    
*   Groq generates grounded responses.
    
*   Responses stream to the frontend.
    
*   Off-topic queries are handled safely.
    
*   Insufficient context results in abstention rather than hallucination.
    
*   P50 latency is calculated.
    
*   P70 latency is calculated.
    
*   P100 latency is calculated.
    
*   Analytics are based on multiple test queries.
    
*   Stage-level timing is visible.
    
*   A live application is deployed.
    
*   A GitHub repository is prepared.
    
*   The project can be demonstrated end-to-end.
    

27\. Hackathon Deliverables
===========================

The final project package should include:

1\. Live Application
--------------------

A deployed, working application.

2\. GitHub Repository
---------------------

Containing:

*   Source code.
    
*   README.
    
*   Setup instructions.
    
*   Architecture diagram.
    
*   Technology stack.
    
*   Chunking methodology.
    
*   Benchmark methodology.
    
*   Latency results.
    
*   Guardrail design.
    

3\. Team/Process Video
----------------------

A 90-second video showing the team development process.

4\. Product Demo Video
----------------------

A demonstration of the complete working system.

5\. Submission Form
-------------------

Final project details and links.

28\. Key Product Differentiators
================================

This project differentiates itself through:

### 1\. Voice-First RAG

The system is designed for spoken interaction rather than simply adding a microphone to a text chatbot.

### 2\. Low-Latency Architecture

The pipeline minimizes unnecessary network and processing overhead.

### 3\. Semantic Cache

Repeated or semantically similar questions can avoid full RAG processing.

### 4\. Embedded Vector Search

LanceDB removes remote vector database network latency from the retrieval path.

### 5\. Advanced Chunking

The system demonstrates deliberate experimentation with semantic, sentence-aware, overlap-aware, and metadata-aware chunking.

### 6\. Guarded Generation

The system is designed to know when it should not answer.

### 7\. Structured Harness

The pipeline is not a raw prompt-to-answer implementation.

### 8\. Transparent Analytics

The user and evaluator can see exactly where time is spent.

29\. Final Product Statement
============================

The final product is a **voice-enabled, ultra-low-latency RAG system with semantic caching, embedded vector retrieval, advanced chunking, structured model orchestration, guardrails, streaming inference, and real-time performance analytics**.

Its purpose is not only to answer questions from the provided MSMARCO-XI dataset, but to demonstrate that every major component of a RAG pipeline can be:

*   Measured.
    
*   Optimized.
    
*   Validated.
    
*   Observed.
    
*   And explained.
    

The system should provide both a compelling user experience and a technically transparent evaluation platform for demonstrating RAG performance.