import React, { useState } from 'react';
import { QrCode, Search, ShieldCheck, AlertTriangle, CheckCircle, Scale, Building, FileCheck, ArrowRight, ExternalLink } from 'lucide-react';

export default function BuyerDeedVerification({ onSelectParcel }) {
  const [searchQuery, setSearchQuery] = useState('P-OD-102');
  const [result, setResult] = useState({
    parcel_id: 'P-OD-102',
    survey_no: '45/0',
    khata_no: '102',
    village: 'Chhatrapur',
    district: 'Ganjam',
    state: 'Odisha',
    owner_name: 'Sudrusti Sethi',
    recorded_area_sqm: 1250.0,
    land_use: 'Agricultural (Clear Title)',
    health_score: 98,
    status: 'CLEAN_VERIFIED',
    checks: [
      { name: 'Revenue Court Stay Status', passed: true, note: 'No pending stay or litigation in Sub-Collector / High Court records' },
      { name: 'Land Acquisition Buffer Flag', passed: true, note: 'Plot not inside NHAI or Industrial Corridor acquisition notification' },
      { name: 'Multiple-Registration Duplicate Check', passed: true, note: 'Single unique registered sale deed on DILRMP / Bhulekh cadastre' },
      { name: 'Aadhaar e-KYC Identity Match', passed: true, note: 'Pattadar identity verified via UIDAI demographic matching' },
      { name: 'Satellite Encroachment Audit', passed: true, note: 'Sentinel-2 multispectral NDVI shows active cropland; 0% illegal concrete built-up' },
      { name: 'Blockchain Immutability Stamp', passed: true, note: 'SHA-256 Approval Hash 0x9f4a... verified on Polygon state ledger' }
    ]
  });

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    // Update sample buyer verification result
    setResult((prev) => ({
      ...prev,
      parcel_id: searchQuery.toUpperCase(),
      survey_no: searchQuery.includes('45') ? '45/0' : '105/A',
      owner_name: searchQuery.includes('45') ? 'Sudrusti Sethi' : 'K. Venkateshwarlu'
    }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 text-center max-w-3xl mx-auto space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto">
          <QrCode className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-extrabold text-slate-100">Public Land Buyer Verification Portal</h2>
        <p className="text-xs text-slate-400 max-w-lg mx-auto">
          Scan a QR code from a registered deed or enter a Parcel / ULPIN ID to check real-time title clarity, court stay orders, and automated fraud risk before purchasing land.
        </p>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex max-w-md mx-auto gap-2 pt-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter Parcel ID (e.g. P-OD-102 or P-105)..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400 transition"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          </div>
          <button
            type="submit"
            className="px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer shadow-lg shadow-cyan-500/20"
          >
            <span>Verify Title</span>
          </button>
        </form>
      </div>

      {/* Verification Result Card */}
      {result && (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 max-w-4xl mx-auto space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-xl font-bold text-slate-100">Parcel {result.parcel_id}</h3>
                <span className="px-3 py-1 rounded-full text-xs font-bold font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>VERIFIED SAFE TO PURCHASE</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Khasra/Survey: <strong>{result.survey_no}</strong> · Khata: <strong>{result.khata_no}</strong> · Village: <strong>{result.village}, {result.district} ({result.state})</strong>
              </p>
            </div>

            {/* Health Meter */}
            <div className="text-right flex items-center gap-3">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-mono block">BhuNetra Health Index</span>
                <span className="text-3xl font-extrabold text-emerald-400 font-mono">{result.health_score}/100</span>
              </div>
            </div>
          </div>

          {/* 6 Key Verification Checks */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-3">
              Automated Due-Diligence & Forensic Checks
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.checks.map((c, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-3">
                  <div className="mt-0.5">
                    {c.passed ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                    )}
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-200 block">{c.name}</span>
                    <span className="text-[11px] text-slate-400">{c.note}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800">
            <span className="text-[11px] text-slate-500 font-mono">
              Certified by Ministry of Rural Development (DILRMP BhuNetra Engine)
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => onSelectParcel && onSelectParcel(result.parcel_id)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition cursor-pointer flex items-center gap-1.5"
              >
                <span>Inspect GIS Boundaries</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => window.open(`/api/certificate/generate/${result.parcel_id}`, '_blank')}
                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition cursor-pointer shadow-lg shadow-emerald-500/20 flex items-center gap-1.5"
              >
                <FileCheck className="w-3.5 h-3.5" />
                <span>Download Land Health Certificate</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
