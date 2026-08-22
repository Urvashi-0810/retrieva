export type Phase = 'idle' | 'permission' | 'listening' | 'vad' | 'transcript' | 'pipeline' | 'answer' | 'complete';

export type Scenario = { 
  query: string; 
  answer: string; 
  grounding: 'GROUNDED' | 'ABSTAINED'; 
  confidence: number; 
  cache: 'HIT' | 'MISS'; 
  latencies: number[];
  sttMs: number;
  ragMs: number;
  p50: number;
  p70: number;
  p100: number;
  route: string;
  chunks: number;
};
