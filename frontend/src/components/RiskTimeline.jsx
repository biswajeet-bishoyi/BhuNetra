/**
 * RiskTimeline.jsx — Phase 4: Temporal risk animation.
 *
 * Lets the user pick a parcel, scrub through the 12-month risk score
 * timeline (fetched from /api/analytics/anomaly-trends), and watch the
 * composite score animate over time. Includes play/pause and speed
 * controls.
 */
import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, FastForward, Rewind, TrendingUp, AlertTriangle, Activity } from 'lucide-react';

const SPEEDS = [
  { id: 'slow',   label: '0.5x', ms: 1200 },
  { id: 'normal', label: '1x',   ms: 600 },
  { id: 'fast',   label: '2x',   ms: 300 },
  { id: 'turbo',  label: '4x',   ms: 120 },
];

const MONTHS = ['Sep\'25','Oct','Nov','Dec','Jan\'26','Feb','Mar','Apr','May','Jun','Jul','Aug'];

// Plot constants
const W = 760;
const H = 260;
const PAD_L = 50;
const PAD_R = 30;
const PAD_T = 30;
const PAD_B = 40;

function riskColor(score) {
  if (score >= 65) return { stroke: '#f43f5e', fill: 'rgba(244,63,94,0.25)', label: 'HIGH' };
  if (score >= 30) return { stroke: '#f59e0b', fill: 'rgba(245,158,11,0.25)', label: 'MODERATE' };
  return { stroke: '#10b981', fill: 'rgba(16,185,129,0.18)', label: 'LOW' };
}

export default function RiskTimeline({ parcelsData, selectedParcelId, onSelectParcel }) {
  const [parcels] = useState(() => {
    if (parcelsData?.features) {
      return parcelsData.features.map(f => ({
        parcel_id: f.properties.parcel_id,
        village: f.properties.village,
      }));
    }
    return [];
  });
  const [activeParcel, setActiveParcel] = useState(selectedParcelId || 'P-105');
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speedId, setSpeedId] = useState('normal');
  const timerRef = useRef(null);

  // Load timeline series
  useEffect(() => {
    setLoading(true);
    setFrame(0);
    fetch('/api/analytics/anomaly-trends')
      .then(r => r.json())
      .then(d => {
        setSeries(d.series || []);
      })
      .catch(() => setSeries([]))
      .finally(() => setLoading(false));
  }, []);

  // Auto-stop at the end of the timeline
  const currentSeries = series.find(s => s.parcel_id === activeParcel);
  const totalFrames = currentSeries?.monthly_scores.length || 0;
  const currentScore = currentSeries?.monthly_scores[frame] ?? 0;

  // Play / pause loop
  useEffect(() => {
    if (!playing) {
      clearTimeout(timerRef.current);
      return;
    }
    if (totalFrames === 0) {
      setPlaying(false);
      return;
    }
    const speed = SPEEDS.find(s => s.id === speedId) || SPEEDS[1];
    timerRef.current = setTimeout(() => {
      setFrame(prev => {
        if (prev + 1 >= totalFrames) {
          setPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, speed.ms);
    return () => clearTimeout(timerRef.current);
  }, [playing, frame, totalFrames, speedId]);

  const handlePlayPause = () => {
    if (totalFrames === 0) return;
    if (!playing && frame >= totalFrames - 1) {
      setFrame(0);
      setTimeout(() => setPlaying(true), 50);
    } else {
      setPlaying(p => !p);
    }
  };

  const handleReset = () => { setFrame(0); setPlaying(false); };
  const handleEnd = () => { setFrame(Math.max(0, totalFrames - 1)); setPlaying(false); };
  const handleScrub = (e) => {
    const v = parseInt(e.target.value, 10);
    setFrame(v);
  };

  // Build path coordinates
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;

  const pointFor = (i, score) => {
    const x = PAD_L + (i / Math.max(totalFrames - 1, 1)) * innerW;
    const y = PAD_T + innerH - (score / 100) * innerH;
    return [x, y];
  };

  const pathD = (() => {
    if (!currentSeries) return '';
    return currentSeries.monthly_scores
      .map((score, i) => {
        const [x, y] = pointFor(i, score);
        return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ');
  })();

  const filledD = (() => {
    if (!currentSeries) return '';
    let head = `M ${PAD_L} ${PAD_T + innerH}`;
    currentSeries.monthly_scores.forEach((score, i) => {
      const [x, y] = pointFor(i, score);
      head += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    });
    head += ` L ${PAD_L + innerW} ${PAD_T + innerH} Z`;
    return head;
  })();

  const [playheadX, playheadY] = pointFor(frame, currentScore);
  const playheadColor = riskColor(currentScore);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              Risk Timeline — Temporal Animation
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Watch how each parcel's fraud-risk score evolves over the last 12 months. The
              ensemble recalculates the composite as satellite, ownership, and OCR signals
              shift through time.
            </p>
          </div>
          <div className="flex items-center gap-2 text-[11px] font-bold">
            <span className="px-2 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300">
              {activeParcel}
            </span>
            <select
              value={activeParcel}
              onChange={e => { setActiveParcel(e.target.value); setFrame(0); setPlaying(false); }}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-[11px] font-semibold focus:outline-none focus:border-amber-500"
            >
              {parcels.map(p => (
                <option key={p.parcel_id} value={p.parcel_id}>
                  {p.parcel_id} · {p.village}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Timeline canvas */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        {loading ? (
          <div className="h-[260px] flex items-center justify-center text-xs text-slate-400">
            Loading 12-month timeline…
          </div>
        ) : !currentSeries ? (
          <div className="h-[260px] flex items-center justify-center text-xs text-slate-400">
            No timeline data available for {activeParcel}.
          </div>
        ) : (
          <div className="relative">
            <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[260px]">
              {/* Threshold bands */}
              <rect x={PAD_L} y={PAD_T} width={innerW} height={innerH * 0.30} fill="rgba(16,185,129,0.04)" />
              <rect x={PAD_L} y={PAD_T + innerH * 0.30} width={innerW} height={innerH * 0.35} fill="rgba(245,158,11,0.05)" />
              <rect x={PAD_L} y={PAD_T + innerH * 0.65} width={innerW} height={innerH * 0.35} fill="rgba(244,63,94,0.05)" />

              {/* Horizontal grid + Y axis labels */}
              {[0, 25, 50, 75, 100].map(t => {
                const y = PAD_T + innerH - (t / 100) * innerH;
                return (
                  <g key={t}>
                    <line x1={PAD_L} y1={y} x2={PAD_L + innerW} y2={y} stroke="#334155" strokeDasharray="2 4" strokeWidth="0.5" />
                    <text x={PAD_L - 8} y={y + 3} textAnchor="end" fontSize="9" fill="#64748b">
                      {t}
                    </text>
                  </g>
                );
              })}

              {/* Risk band labels (right side) */}
              <text x={PAD_L + innerW + 4} y={PAD_T + 10} fontSize="8" fill="#10b981">LOW</text>
              <text x={PAD_L + innerW + 4} y={PAD_T + innerH * 0.30 + 4} fontSize="8" fill="#f59e0b">MOD</text>
              <text x={PAD_L + innerW + 4} y={PAD_T + innerH * 0.65 + 4} fontSize="8" fill="#f43f5e">HIGH</text>

              {/* X axis month labels */}
              {MONTHS.map((m, i) => {
                const x = PAD_L + (i / Math.max(totalFrames - 1, 1)) * innerW;
                return (
                  <text key={i} x={x} y={H - 12} textAnchor="middle" fontSize="9" fill="#64748b">
                    {m}
                  </text>
                );
              })}

              {/* Filled area */}
              <path d={filledD} fill={playheadColor.fill} />

              {/* Line */}
              <path d={pathD} fill="none" stroke={playheadColor.stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

              {/* Past dots */}
              {currentSeries.monthly_scores.map((s, i) => {
                const [x, y] = pointFor(i, s);
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r={i === frame ? 5 : 2.5}
                    fill={i === frame ? playheadColor.stroke : '#475569'}
                    stroke={i === frame ? '#0f172a' : 'none'}
                    strokeWidth={i === frame ? 2 : 0}
                  />
                );
              })}

              {/* Playhead vertical line */}
              <line x1={playheadX} y1={PAD_T} x2={playheadX} y2={PAD_T + innerH} stroke={playheadColor.stroke} strokeWidth="1" strokeDasharray="3 3" opacity="0.7" />
            </svg>

            {/* Floating score badge over playhead */}
            <div
              className="absolute pointer-events-none"
              style={{
                left: `${(playheadX / W) * 100}%`,
                top: `${(playheadY / H) * 100}%`,
                transform: 'translate(-50%, -130%)',
              }}
            >
              <div className={`px-2.5 py-1 rounded-lg border text-[10px] font-bold shadow-md whitespace-nowrap ${
                currentScore >= 65
                  ? 'bg-rose-500/20 border-rose-500/40 text-rose-200'
                  : currentScore >= 30
                  ? 'bg-amber-500/20 border-amber-500/40 text-amber-200'
                  : 'bg-emerald-500/20 border-emerald-500/40 text-emerald-200'
              }`}>
                {currentScore.toFixed(1)} · {playheadColor.label}
              </div>
            </div>
          </div>
        )}

        {/* Scrub slider */}
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={handleReset}
            disabled={!currentSeries}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 border border-slate-700 cursor-pointer"
            title="Reset to start"
          >
            <Rewind className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handlePlayPause}
            disabled={!currentSeries}
            className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 text-xs font-bold flex items-center gap-1.5 cursor-pointer"
          >
            {playing ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{playing ? 'Pause' : 'Play'}</span>
          </button>
          <button
            onClick={handleEnd}
            disabled={!currentSeries}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 border border-slate-700 cursor-pointer"
            title="Jump to end"
          >
            <FastForward className="w-3.5 h-3.5" />
          </button>

          <input
            type="range"
            min="0"
            max={Math.max(totalFrames - 1, 0)}
            value={frame}
            onChange={handleScrub}
            className="flex-1 accent-amber-500"
            disabled={!currentSeries}
          />

          <div className="text-[10px] font-bold text-slate-400 tabular-nums min-w-[60px] text-right">
            {totalFrames > 0 ? `${frame + 1} / ${totalFrames}` : '0 / 0'}
          </div>

          {/* Speed selector */}
          <div className="flex items-center gap-1 ml-2">
            {SPEEDS.map(s => (
              <button
                key={s.id}
                onClick={() => setSpeedId(s.id)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-bold border cursor-pointer ${
                  speedId === s.id
                    ? 'bg-amber-500/20 text-amber-200 border-amber-500/40'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Score summary at the current frame */}
      {currentSeries && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SummaryCard
            icon={Activity}
            label="Current Score"
            value={currentScore.toFixed(1)}
            tint={currentScore >= 65 ? 'rose' : currentScore >= 30 ? 'amber' : 'emerald'}
          />
          <SummaryCard
            icon={TrendingUp}
            label="Peak (12mo)"
            value={Math.max(...currentSeries.monthly_scores).toFixed(1)}
            tint="amber"
          />
          <SummaryCard
            icon={AlertTriangle}
            label="Lowest (12mo)"
            value={Math.min(...currentSeries.monthly_scores).toFixed(1)}
            tint="emerald"
          />
          <SummaryCard
            icon={Activity}
            label="Avg (12mo)"
            value={(currentSeries.monthly_scores.reduce((a,b) => a+b, 0) / currentSeries.monthly_scores.length).toFixed(1)}
            tint="slate"
          />
        </div>
      )}
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, tint = 'slate' }) {
  const tones = {
    rose:    'border-rose-500/30 bg-rose-500/10 text-rose-200',
    amber:   'border-amber-500/30 bg-amber-500/10 text-amber-200',
    emerald: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
    slate:   'border-slate-700 bg-slate-900 text-slate-200',
  };
  return (
    <div className={`rounded-2xl border p-4 ${tones[tint] || tones.slate}`}>
      <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider opacity-80">
        <Icon className="w-3 h-3" />
        <span>{label}</span>
      </div>
      <p className="text-2xl font-extrabold mt-1.5 tabular-nums">{value}</p>
    </div>
  );
}
