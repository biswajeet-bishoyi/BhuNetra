import React from 'react';
import { X, CheckCircle2, AlertTriangle, Cpu, ShieldAlert, FileCheck, Scale, Lock } from 'lucide-react';

export default function StatusModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const modules = [
    { name: 'Engine 1: Registry OCR', tag: 'REAL (Narrow) / FALLBACK', detail: 'PaddleOCR / Regex layout parser extracting Telangana Dharani deeds', color: 'emerald' },
    { name: 'Engine 2: GIS Validation', tag: 'REAL', detail: 'In-memory Shapely STRtree topology checks + scikit-learn Isolation Forest (Zero SpatiaLite extension)', color: 'emerald' },
    { name: 'Engine 3: Ownership Intelligence', tag: 'RULE-STUB', detail: 'Rapid resale frequency (>3 transfers in <30 days) and title graph analysis', color: 'amber' },
    { name: 'Engine 4: Satellite Cross-Check', tag: 'RULE-STUB / MOCK', detail: 'Pre-downloaded Sentinel-2 Shamshabad/Mamidipally scene (zero live API calls)', color: 'amber' },
    { name: 'Engine 5: Fraud Risk Ensemble', tag: 'REAL', detail: 'Deterministic 35/25/25/15 weighted combination into Green/Yellow/Red with SHAP explanations', color: 'emerald' },
    { name: 'Officer Review Queue & Audit Log', tag: 'REAL', detail: 'Human-in-the-loop queue with mandatory typed reasons and Sec 65B audit log', color: 'emerald' },
    { name: 'Revenue Court Status Field', tag: 'REAL', detail: 'Parcel litigation status tracking (Clean / Stay Order / Mutation Pending / Court Case)', color: 'emerald' },
    { name: 'Blockchain Approval Hashing', tag: 'REAL / FALLBACK', detail: 'SHA-256 cryptographic approval hashing + Solidity smart contract for audit trail', color: 'emerald' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">BhuNetra AI — Module Implementation Tiers</h2>
            <p className="text-xs text-slate-400">SIH 2026 Scope Transparency & Fallback Declaration (STATUS.md)</p>
          </div>
        </div>

        <div className="space-y-2.5 my-4 max-h-[50vh] overflow-y-auto pr-1">
          {modules.map((m, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start justify-between gap-3">
              <div>
                <h4 className="text-xs font-semibold text-slate-200">{m.name}</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">{m.detail}</p>
              </div>
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border shrink-0 ${
                  m.tag.startsWith('REAL')
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                }`}
              >
                {m.tag}
              </span>
            </div>
          ))}
        </div>

        {/* Legal & Separation of Concerns Notes */}
        <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
          <p className="font-semibold text-slate-300">Architectural & Legal Notes:</p>
          <p>• <span className="text-amber-300">Spatial Separation:</span> Spatial data & processing live in Python via GeoPandas/Shapely (PostGIS production path); chain stays scoped to hash-only.</p>
          <p>• <span className="text-amber-300">DPDP Act 2023:</span> Data minimization applied to Citizen views.</p>
          <p>• <span className="text-amber-300">Registration Act 1908:</span> Hashes provide audit integrity under IT Act Sec 65B; statutory ownership remains with the registered deed.</p>
        </div>

        <div className="pt-3 mt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Zero live external network API calls during demo presentation.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-bold hover:bg-amber-400 transition"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
