'use client'

import { useEffect, useMemo, useState, useRef } from 'react'
import { Activity, AudioLines, CheckCircle2, Database, Mic, Radio, ShieldCheck, Sparkles, Waves, Zap } from 'lucide-react'

import { Phase, Scenario } from './types'
const scenarios: Scenario[] = [
  {
    query: 'How does the retrieval cache improve response time?',
    answer: 'The retrieval cache stores recent embedding lookups and ranked evidence so repeated questions skip expensive retrieval work. In this run, the cache returned a warm match and saved 42 milliseconds.',
    grounding: 'GROUNDED',
    confidence: 94,
    cache: 'HIT',
    latencies: [34, 72, 18, 9, 41, 22, 116],
    sttMs: 48,
    ragMs: 90,
    p50: 11.1,
    p70: 12.8,
    p100: 21.2,
    route: 'Semantic Cache → LanceDB',
    chunks: 5
  },
  {
    query: 'What is the weather on Mars tomorrow?',
    answer: 'I can’t answer that from the connected knowledge base. This question is outside the available evidence, so I’m abstaining rather than guessing.',
    grounding: 'ABSTAINED',
    confidence: 18,
    cache: 'MISS',
    latencies: [34, 69, 21, 18, 49, 38, 62],
    sttMs: 52,
    ragMs: 142,
    p50: 18.4,
    p70: 24.1,
    p100: 48.6,
    route: 'LanceDB Hybrid Search',
    chunks: 0
  },
]

function Waveform({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let audioContext: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let microphone: MediaStreamAudioSourceNode | null = null;
    let stream: MediaStream | null = null;
    let animationFrameId: number;
    const dataArray = new Uint8Array(256);

    const initAudio = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 512;
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);
      } catch (err) {
        console.error('Error accessing microphone', err);
      }
    };

    if (active) {
      initAudio();
    }

    let smoothedVolume = 0;

    const draw = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      if (analyser && active) {
        analyser.getByteTimeDomainData(dataArray);
      } else {
        // Fallback flat line when not active
        for (let i = 0; i < dataArray.length; i++) dataArray[i] = 128;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] - 128;
        sum += Math.abs(v);
      }
      const volume = sum / dataArray.length;

      // Smooth the volume over time to avoid jerky movements
      smoothedVolume = smoothedVolume * 0.85 + volume * 0.15;

      const globalAmplitude = active ? 0.15 + (smoothedVolume / 128) * 8 : 0.15;
      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;
      const K = 2; // X-axis scale

      const drawWave = (color: string, opt: { amplitude: number, speed: number, phaseOffset: number, lineWidth: number, opacity: number }) => {
        ctx.beginPath();
        ctx.lineWidth = opt.lineWidth;
        ctx.strokeStyle = color;
        ctx.globalAlpha = opt.opacity;

        const time = Date.now() / 1000;
        const phase = time * opt.speed + opt.phaseOffset;

        for (let x_pixel = 0; x_pixel <= width; x_pixel += 2) {
          const x = (x_pixel / width) * 2 * K - K; // maps to [-2, 2]

          // Standard Siri wave attenuation
          const attenuation = 4 / (4 + Math.pow(x, 4));

          // Pure sine wave modulated by smoothed audio volume
          const sineHeight = Math.sin(x * 3 + phase) * opt.amplitude * globalAmplitude * (height / 3) * attenuation;

          const y = centerY + sineHeight;

          if (x_pixel === 0) {
            ctx.moveTo(x_pixel, y);
          } else {
            ctx.lineTo(x_pixel, y);
          }
        }
        ctx.stroke();
      };

      // Siri Wave styled colorful lines
      drawWave('#38bdf8', { amplitude: 1.0, speed: 2.0, phaseOffset: 0, lineWidth: 2, opacity: 1.0 }); // Cyan
      drawWave('#a78bfa', { amplitude: -0.7, speed: 1.5, phaseOffset: Math.PI / 2, lineWidth: 2.5, opacity: 0.8 }); // Violet
      drawWave('#34d399', { amplitude: 0.5, speed: 2.5, phaseOffset: Math.PI, lineWidth: 2, opacity: 0.6 }); // Emerald
      drawWave('#f0abfc', { amplitude: -0.3, speed: 3.0, phaseOffset: Math.PI * 1.5, lineWidth: 1.5, opacity: 0.5 }); // Fuchsia

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (stream) stream.getTracks().forEach(track => track.stop());
      if (audioContext && audioContext.state !== 'closed') audioContext.close();
    };
  }, [active]);

  return (
    <div className={`voice-waves ${active ? 'voice-waves-active' : ''}`} aria-label="Live audio waveform">
      <canvas ref={canvasRef} width={450} height={200} style={{ width: '100%', height: '100%' }} />
    </div>
  );
}
function Gauge({ value, label, color = 'violet' }: { value: number; label: string; color?: string }) { return <div className="relative grid size-24 place-items-center rounded-full" style={{ background: `conic-gradient(var(--${color}) ${value * 3.6}deg, rgba(255,255,255,.12) 0deg)` }}><div className="grid size-[76px] place-items-center rounded-full bg-slate-950/70"><div className="text-center"><div className="font-mono text-lg font-bold text-white">{value}%</div><div className="text-[9px] tracking-[.16em] text-slate-400">{label}</div></div></div></div> }

export default function Page() {
  const [phase, setPhase] = useState<Phase>('idle'); const [scenarioIndex, setScenarioIndex] = useState(0); const [transcript, setTranscript] = useState(''); const [answer, setAnswer] = useState(''); const [stage, setStage] = useState(-1); const [count, setCount] = useState(0)
  const data = scenarios[scenarioIndex]; const active = phase !== 'idle' && phase !== 'complete'; const resultsReady = phase === 'complete'; const status = phase === 'vad' ? 'LISTENING' : phase === 'transcript' || phase === 'pipeline' ? 'PROCESSING' : phase === 'answer' ? 'STREAMING' : phase.toUpperCase()
  useEffect(() => { if (phase === 'idle') return; const timers: ReturnType<typeof setTimeout>[] = []; if (phase === 'permission') timers.push(setTimeout(() => setPhase('listening'), 650)); if (phase === 'listening') timers.push(setTimeout(() => setPhase('vad'), 850)); if (phase === 'vad') timers.push(setTimeout(() => setPhase('transcript'), 900)); if (phase === 'transcript') { let i = 0; const t = setInterval(() => { setTranscript(data.query.slice(0, i)); i += 2; if (i > data.query.length) { clearInterval(t); setPhase('pipeline') } }, 42); return () => clearInterval(t) }; if (phase === 'pipeline') { const t = setTimeout(() => setPhase('answer'), 400); return () => clearTimeout(t) }; if (phase === 'answer') { let i = 0; const t = setInterval(() => { setAnswer(data.answer.slice(0, i)); i += 3; if (i > data.answer.length) { clearInterval(t); setPhase('complete') } }, 25); return () => clearInterval(t) }; return () => timers.forEach(clearTimeout) }, [phase, data])
  useEffect(() => { if (!resultsReady) return; setTimeout(() => document.getElementById('analytics-header')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100); let i = 0; const t = setInterval(() => { i += 4; setCount(Math.min(100, i)); if (i >= 100) clearInterval(t) }, 18); return () => clearInterval(t) }, [resultsReady])
  const start = () => { if (active) return; setScenarioIndex((scenarioIndex + 1) % scenarios.length); setTranscript(''); setAnswer(''); setStage(-1); setCount(0); setPhase('permission') }; const displayTranscript = transcript || (phase === 'idle' || resultsReady ? data.query : 'Listening for a question...'); const total = useMemo(() => data.latencies.reduce((a, b) => a + b, 0), [data])
  return <main className="min-h-screen bg-slate-950 text-white selection:bg-cyan-300/30">
    <div className="mesh" />
    <div className="relative mx-auto max-w-[1180px] px-5 py-5 lg:px-8 lg:py-7">
      <header className="flex items-center justify-between border-b border-white/10 pb-5">
        <div className="flex items-center gap-3">
          <div className="grid size-9 place-items-center rounded-xl bg-violet-600 text-white shadow-lg shadow-violet-950/40"><Waves size={19} /></div>
          <div><div className="font-mono text-sm font-bold tracking-[.2em]">ECHORAG</div><div className="text-[10px] tracking-[.18em] text-slate-400">VOICE RETRIEVAL INSTRUMENT</div></div>
        </div>
      </header>

      <section className="mx-auto flex max-w-3xl flex-col items-center py-12 text-center lg:py-16">
        <div className={`mic-orbit ${active ? 'orbit-active' : ''}`}><div className="orbit-ring" /><Waveform active={active} />
          <button aria-label="Start voice query" onClick={start} className={`mic-button ${active ? 'mic-running' : ''}`}><Mic size={48} strokeWidth={1.5} /></button>
        </div>
        <div className="mt-5 font-mono text-xs font-bold tracking-[.24em] text-white">{phase === 'idle' || resultsReady ? 'TAP TO SPEAK' : phase === 'vad' ? 'SPEECH DETECTED' : phase === 'listening' ? 'LISTENING...' : phase === 'answer' ? 'STREAMING ANSWER' : 'PROCESSING...'}</div>
        <div className="mt-2 text-xs text-slate-400">{resultsReady ? 'Run another query to compare results' : 'Ask a question and watch the evidence path unfold'}</div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Panel title="LIVE TRANSCRIPT" icon={<AudioLines size={15} />} active={phase === 'transcript'}>
          <div className="min-h-44"><div className="mb-5 flex items-center gap-2 font-mono text-[10px] tracking-[.14em] text-cyan-200"><span className="record-dot" /> VOICE INPUT / VAD {phase === 'vad' ? 'SPEECH DETECTED' : 'READY'}</div><p className="text-lg leading-relaxed text-white">{displayTranscript}<span className={active && phase === 'transcript' ? 'cursor' : ''} /></p></div>
        </Panel>
        <Panel title="GENERATED ANSWER" icon={<Zap size={15} />} active={phase === 'answer'}>
          <div className="min-h-44"><div className={`mb-5 inline-flex items-center gap-2 rounded-md px-2 py-1 font-mono text-[10px] tracking-wider ${data.grounding === 'GROUNDED' ? 'bg-emerald-300/10 text-emerald-200' : 'bg-rose-300/10 text-rose-200'}`}><ShieldCheck size={13} /> {resultsReady ? data.grounding : 'AWAITING GROUNDING'}</div><p className="text-[15px] leading-7 text-slate-200">{answer || (resultsReady ? data.answer : 'Your grounded response will appear here after the voice path completes.')}<span className={phase === 'answer' ? 'cursor' : ''} /></p></div>
        </Panel>
      </section>

      {resultsReady && (() => {
        const breakdown = [
          { label: 'Voice activity (VAD)', value: data.latencies[0] },
          { label: 'Speech-to-text', value: data.latencies[1] },
          { label: 'Embedding', value: data.latencies[2] },
          { label: 'Cache lookup', value: data.latencies[3] },
          { label: 'Vector retrieval', value: data.latencies[4] },
          { label: 'Guardrail check', value: data.latencies[5] },
        ];
        const genValue = data.latencies[6];
        const retrievalTotal = breakdown.reduce((a, b) => a + b.value, 0);
        const e2eTotal = retrievalTotal + genValue;

        return (
          <section className="animate-results mx-auto mt-12 max-w-5xl space-y-8">
            <div className="flex flex-col items-center justify-center space-y-3 pb-2 text-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 font-mono text-[10px] tracking-widest text-cyan-300">
                <Activity size={12} />
                PIPELINE TELEMETRY
              </div>
              <h2 id="analytics-header" className="text-2xl font-semibold tracking-tight text-white">Execution Analytics</h2>
            </div>

            <div className="grid gap-6 md:grid-cols-[1.5fr_1fr]">
              {/* Left Panel: Clean Breakdown */}
              <div className="rounded-3xl border border-white/5 bg-slate-900/50 p-8 shadow-2xl backdrop-blur-xl">
                <div className="mb-6 flex items-center justify-between font-mono text-xs font-bold tracking-widest text-slate-400 border-b border-white/5 pb-4">
                  <span className="text-xl text-cyan-400">RETRIEVAL CORE</span>
                  <span className='text-sm'>{(retrievalTotal * count / 100).toFixed(1)}ms <span className="opacity-50">/ 200ms</span></span>
                </div>

                <div className="mb-8 space-y-5">
                  {breakdown.map(item => (
                    <div key={item.label} className="flex items-center gap-5 font-mono text-[13px]">
                      <span className="w-56 text-slate-300">{item.label}</span>
                      <div className="flex h-2 flex-1 overflow-hidden rounded-full bg-black/40">
                        <div className="h-full bg-cyan-400/80 transition-all duration-500" style={{ width: `${(item.value / 150) * 100}%` }} />
                      </div>
                      <span className="w-20 text-l text-right font-medium text-cyan-300">{(item.value * count / 100).toFixed(1)}ms</span>
                    </div>
                  ))}
                </div>

                <div className="mb-6 flex items-center justify-between font-mono text-xs font-bold tracking-widest text-slate-400 border-b border-white/5 pb-4">
                  <span className="text-xl text-violet-400">GENERATION</span>
                  <span className="text-sm opacity-50">Latency</span>
                </div>

                <div className="space-y-5">
                  <div className="flex items-center gap-5 font-mono text-[13px]">
                    <span className="w-56 text-slate-300">LLM Response</span>
                    <div className="flex h-2 flex-1 overflow-hidden rounded-full bg-black/40">
                      <div className="h-full bg-violet-500/80 transition-all duration-500" style={{ width: `100%` }} />
                    </div>
                    <span className="w-20 text-right font-medium text-violet-300">{(genValue * count / 100).toFixed(1)}ms</span>
                  </div>
                </div>
              </div>

              {/* Right Panel: Summaries & Evidence */}
              <div className="flex flex-col gap-6">
                <div className="flex-1 rounded-3xl border border-white/5 bg-slate-900/50 p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden group">
                  <div className="absolute -right-12 -top-12 size-48 rounded-full bg-emerald-500/10 blur-3xl transition-transform group-hover:scale-110" />
                  <div className="font-mono text-[10px] font-bold tracking-widest text-emerald-400">END-TO-END LATENCY</div>
                  <div className="mt-4 flex items-baseline gap-1 relative z-10">
                    <span className="font-mono text-5xl font-bold tracking-tighter text-white">{(e2eTotal * count / 100).toFixed(1)}</span>
                    <span className="font-mono text-sm text-emerald-400">ms</span>
                  </div>
                  <div className="mt-6 border-t border-white/5 pt-4 font-mono text-[10px] leading-relaxed text-slate-400 relative z-10">
                    <div className="mb-2 text-cyan-300">ROUTE: {data.route}</div>
                    Cache status: {data.cache}
                  </div>
                </div>

                <div className="flex-1 rounded-3xl border border-white/5 bg-slate-900/50 p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden">
                  <div className="font-mono text-[10px] font-bold tracking-widest text-slate-400 mb-6 border-b border-white/5 pb-4">RETRIEVAL EVIDENCE</div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="font-mono text-3xl font-bold text-white">{data.chunks}</div>
                      <div className="mt-2 font-mono text-[9px] tracking-widest text-slate-500">CHUNKS</div>
                    </div>
                    <div>
                      <div className="font-mono text-3xl font-bold text-white">{data.confidence}%</div>
                      <div className="mt-2 font-mono text-[9px] tracking-widest text-slate-500">CONFIDENCE</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        );
      })()}
    </div>
  </main>
}
function Panel({ title, icon, children, active }: { title: string; icon: React.ReactNode; children: React.ReactNode; active?: boolean }) { return <div className={`panel ${active ? 'panel-active' : ''}`}><div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3"><div className="flex items-center gap-2 font-mono text-[10px] font-bold tracking-[.14em] text-slate-300">{icon}{title}</div><span className="font-mono text-[9px] text-slate-500">{active ? 'LIVE' : 'READY'}</span></div>{children}</div> }

