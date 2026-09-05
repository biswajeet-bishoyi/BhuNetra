import React, { useState, useEffect, useRef } from 'react';
import {
  Scale,
  FileCheck,
  CheckCircle2,
  AlertTriangle,
  Download,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  Clock,
  Sparkles,
  Search,
  ExternalLink,
  ChevronRight,
  FileText,
  MapPin,
  Building,
  Check,
  X,
  Zap,
  ArrowDown
} from 'lucide-react';

export default function OfficerTripleWorkspace({ onSelectParcel }) {
  const [selectedParcelId, setSelectedParcelId] = useState('P-OD-102');
  const [loading, setLoading] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [duplicateClaims, setDuplicateClaims] = useState([]);
  const [activeClaim, setActiveClaim] = useState(null);
  const [simulateDuplicateClaim, setSimulateDuplicateClaim] = useState(false);
  const [justEvaluated, setJustEvaluated] = useState(false);
  const [officerNotes, setOfficerNotes] = useState(
    'Three-way evidence aligns with historical mutation orders. Section 65B IT Act admissibility confirmed.'
  );
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [decisionSuccess, setDecisionSuccess] = useState(null);

  const resultsRef = useRef(null);

  // 3 Document Ingest States (Registration vs Revenue vs Survey)
  const [doc1Reg, setDoc1Reg] = useState({
    owner_name: 'Sudrusti Sethi',
    father_name: 'P. Sethi',
    survey_no: '45/0',
    khata_no: '102',
    area_sqm: '1250',
    village: 'Chhatrapur',
    district: 'Ganjam',
    registration_no: 'REG-2026-OD-8841',
    deed_date: '2026-08-15'
  });

  const [doc2Rev, setDoc2Rev] = useState({
    owner_name: 'Sudrusti Sethi',
    father_name: 'P. Sethi',
    survey_no: '45/0',
    khata_no: '102',
    area_sqm: '1250',
    village: 'Chhatrapur',
    district: 'Ganjam',
    revenue_court_status: 'Clean (No Stay)',
    khatauni_no: 'KH-102-OD'
  });

  const [doc3Sur, setDoc3Sur] = useState({
    owner_name: 'S. Sethi',
    father_name: 'P. Sethi',
    survey_no: '45/0',
    area_sqm: '1248',
    village: 'Chhatrapur',
    district: 'Ganjam',
    boundary_integrity: 'Verified (0% Encroachment)',
    gps_coordinates: '19.3541° N, 84.9872° E'
  });

  useEffect(() => {
    runComparison();
    fetchDuplicateClaims();
  }, [selectedParcelId]);

  const fetchDuplicateClaims = async () => {
    try {
      const res = await fetch('/api/title-chain/duplicate-claims');
      if (res.ok) {
        const json = await res.json();
        setDuplicateClaims(json.claims || []);
        if (json.claims && json.claims.length > 0) {
          setActiveClaim(json.claims[0]);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const runComparison = async (overrideDocs = null, overrideDuplicate = null, shouldScroll = false) => {
    setLoading(true);
    setDecisionSuccess(null);
    try {
      const reg = overrideDocs?.doc1 || doc1Reg;
      const rev = overrideDocs?.doc2 || doc2Rev;
      const sur = overrideDocs?.doc3 || doc3Sur;
      const hasDup = overrideDuplicate !== null ? overrideDuplicate : simulateDuplicateClaim;

      const payload = {
        parcel_id: selectedParcelId,
        registration_doc: reg,
        revenue_doc: rev,
        survey_doc: sur,
        historical_chain_continuous: true,
        has_duplicate_claim: hasDup && activeClaim !== null
      };

      const res = await fetch('/api/title-chain/triple-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const json = await res.json();
        setComparisonResult(json);
        setJustEvaluated(true);
        setTimeout(() => setJustEvaluated(false), 2500);

        if (shouldScroll) {
          setTimeout(() => {
            resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 100);
        }
      }
    } catch (e) {
      console.error('Comparison error', e);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    setGeneratingPdf(true);
    try {
      window.open(
        `/api/title-chain/evidence-package/${selectedParcelId}/pdf?officer_notes=${encodeURIComponent(
          officerNotes
        )}`,
        '_blank'
      );
    } catch (e) {
      console.error('PDF export failed', e);
    } finally {
      setTimeout(() => setGeneratingPdf(false), 1500);
    }
  };

  const handleClaimAction = async (claimId, action) => {
    try {
      const res = await fetch(
        `/api/title-chain/duplicate-claims/${claimId}/resolve?action=${action}&officer_notes=${encodeURIComponent(
          officerNotes
        )}`,
        { method: 'POST' }
      );
      if (res.ok) {
        setDecisionSuccess(`Duplicate Claim #${claimId} resolved (${action})`);
        fetchDuplicateClaims();
        runComparison();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
              Revenue Officer Decision Support Workspace
            </span>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
              IT Act 2000 Sec 65B Admissible
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-slate-100 mt-1">
            Three-Way Evidence Comparison &amp; Ownership Confidence Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Cross-examines <strong>Registered Deed (35%)</strong>, <strong>Revenue Record (25%)</strong>,{' '}
            <strong>Cadastral Survey (25%)</strong>, and <strong>Title Chain (15%)</strong> with automated conflict screening.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={runComparison}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Re-Evaluate</span>
          </button>
          <button
            onClick={handleDownloadPdf}
            disabled={generatingPdf}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs font-black shadow-lg shadow-amber-500/20 transition cursor-pointer disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            <span>{generatingPdf ? 'Generating PDF…' : 'Export Court Evidence PDF'}</span>
          </button>
        </div>
      </div>

      {/* Feature 5 & 9: Conflicting Duplicate Claim Alert Banner */}
      {duplicateClaims.length > 0 && (
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-200 animate-fade-in shadow-xl shadow-rose-950/20">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-rose-500/20 border border-rose-500/30 shrink-0">
                <AlertTriangle className="w-5 h-5 text-rose-400" />
              </div>
              <div>
                <h3 className="text-sm font-extrabold text-rose-100 flex items-center gap-2">
                  High-Risk Duplicate Ownership Claim Detected
                  <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500 text-slate-950 font-black">
                    {activeClaim?.conflict_score}% Conflict
                  </span>
                </h3>
                <p className="text-xs text-rose-300/90 mt-1">
                  Survey #{activeClaim?.survey_no} is already registered to{' '}
                  <strong className="text-emerald-300">{activeClaim?.existing_owner}</strong>. New claimant{' '}
                  <strong className="text-white">{activeClaim?.new_claimant}</strong> filed a conflicting title deed.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 self-end md:self-auto">
              <button
                onClick={() => handleClaimAction(activeClaim?.id || 99, 'DISMISS')}
                className="px-3 py-1.5 rounded-lg bg-rose-900/60 hover:bg-rose-900 text-rose-200 border border-rose-700 text-xs font-bold transition cursor-pointer"
              >
                Dismiss Fake Claim
              </button>
              <button
                onClick={() => handleClaimAction(activeClaim?.id || 99, 'CALL_FOR_HEARING')}
                className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black transition cursor-pointer"
              >
                Issue Notice For Hearing
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Feature 6: Triple Document Workspace Ingest Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Source 1: Registered Sale Deed */}
        <div className="glass-panel rounded-2xl p-4 border border-slate-800 bg-slate-900/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-extrabold uppercase text-amber-400 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" />
                1. Registered Deed (35%)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                Primary Title
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block">Pattadar / Owner</label>
                <input
                  type="text"
                  value={doc1Reg.owner_name}
                  onChange={(e) => setDoc1Reg({ ...doc1Reg, owner_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-amber-300 font-bold focus:outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 block">Survey No.</label>
                  <input
                    type="text"
                    value={doc1Reg.survey_no}
                    onChange={(e) => setDoc1Reg({ ...doc1Reg, survey_no: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block">Extent (sq.m)</label>
                  <input
                    type="text"
                    value={doc1Reg.area_sqm}
                    onChange={(e) => setDoc1Reg({ ...doc1Reg, area_sqm: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block">Registration Number</label>
                <input
                  type="text"
                  value={doc1Reg.registration_no}
                  onChange={(e) => setDoc1Reg({ ...doc1Reg, registration_no: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-300 text-xs focus:outline-none"
                />
              </div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Sub-Registrar Ganjam</span>
            <span className="text-emerald-400 font-semibold">✓ Stamp Duty Paid</span>
          </div>
        </div>

        {/* Source 2: Revenue Record (RoR / Khatauni) */}
        <div className="glass-panel rounded-2xl p-4 border border-slate-800 bg-slate-900/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-extrabold uppercase text-cyan-400 flex items-center gap-1.5">
                <Building className="w-3.5 h-3.5" />
                2. Revenue RoR (25%)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                Bhulekh Khata
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block">Khatedar Name</label>
                <input
                  type="text"
                  value={doc2Rev.owner_name}
                  onChange={(e) => setDoc2Rev({ ...doc2Rev, owner_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-cyan-300 font-bold focus:outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 block">Khata No.</label>
                  <input
                    type="text"
                    value={doc2Rev.khata_no}
                    onChange={(e) => setDoc2Rev({ ...doc2Rev, khata_no: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block">Survey No.</label>
                  <input
                    type="text"
                    value={doc2Rev.survey_no}
                    onChange={(e) => setDoc2Rev({ ...doc2Rev, survey_no: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block">Revenue Court Status</label>
                <input
                  type="text"
                  value={doc2Rev.revenue_court_status}
                  onChange={(e) => setDoc2Rev({ ...doc2Rev, revenue_court_status: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-emerald-400 font-semibold focus:outline-none"
                />
              </div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Tahasildar Chhatrapur</span>
            <span className="text-emerald-400 font-semibold">✓ Mutation Approved</span>
          </div>
        </div>

        {/* Source 3: Cadastral Survey & Ground Report */}
        <div className="glass-panel rounded-2xl p-4 border border-slate-800 bg-slate-900/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-extrabold uppercase text-emerald-400 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5" />
                3. Cadastral Survey (25%)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                Ground GPS
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block">Survey Owner / Occupant</label>
                <input
                  type="text"
                  value={doc3Sur.owner_name}
                  onChange={(e) => setDoc3Sur({ ...doc3Sur, owner_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-emerald-300 font-bold focus:outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 block">Plot Survey</label>
                  <input
                    type="text"
                    value={doc3Sur.survey_no}
                    onChange={(e) => setDoc3Sur({ ...doc3Sur, survey_no: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block">Measured Extent</label>
                  <input
                    type="text"
                    value={doc3Sur.area_sqm}
                    onChange={(e) => setDoc3Sur({ ...doc3Sur, area_sqm: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block">Boundary Demarcation</label>
                <input
                  type="text"
                  value={doc3Sur.boundary_integrity}
                  onChange={(e) => setDoc3Sur({ ...doc3Sur, boundary_integrity: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-300 text-xs focus:outline-none"
                />
              </div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>DILRMP DGPS Cadastre</span>
            <span className="text-emerald-400 font-semibold">✓ 0% Encroachment</span>
          </div>
        </div>
      </div>

      {/* Evaluate & Scenario Control Toolbar */}
      <div className="glass-panel rounded-2xl p-4 border border-amber-500/40 bg-gradient-to-r from-slate-900 via-slate-900/95 to-amber-950/30 shadow-2xl shadow-slate-950/60 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5 mr-1">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Test Scenarios:</span>
          </span>
          <button
            type="button"
            onClick={() => {
              const d1 = {
                owner_name: 'Sudrusti Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                khata_no: '102',
                area_sqm: '1250',
                village: 'Chhatrapur',
                district: 'Ganjam',
                registration_no: 'REG-2026-OD-8841',
                deed_date: '2026-08-15'
              };
              const d2 = {
                owner_name: 'Sudrusti Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                khata_no: '102',
                area_sqm: '1250',
                village: 'Chhatrapur',
                district: 'Ganjam',
                revenue_court_status: 'Clean (No Stay)',
                khatauni_no: 'KH-102-OD'
              };
              const d3 = {
                owner_name: 'Sudrusti Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                area_sqm: '1250',
                village: 'Chhatrapur',
                district: 'Ganjam',
                boundary_integrity: 'Verified (0% Encroachment)',
                gps_coordinates: '19.3541° N, 84.9872° E'
              };
              setDoc1Reg(d1);
              setDoc2Rev(d2);
              setDoc3Sur(d3);
              setSimulateDuplicateClaim(false);
              runComparison({ doc1: d1, doc2: d2, doc3: d3 }, false, true);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900 border border-emerald-500/50 text-emerald-300 text-xs font-bold transition cursor-pointer flex items-center gap-1.5"
          >
            <span>✓ 100% Perfect Match</span>
          </button>
          <button
            type="button"
            onClick={() => {
              const d1 = {
                owner_name: 'Sudrusti Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                khata_no: '102',
                area_sqm: '1250',
                village: 'Chhatrapur',
                district: 'Ganjam',
                registration_no: 'REG-2026-OD-8841',
                deed_date: '2026-08-15'
              };
              const d2 = {
                owner_name: 'Sudrusti Seth',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                khata_no: '102',
                area_sqm: '1250',
                village: 'Chhatrapur',
                district: 'Ganjam',
                revenue_court_status: 'Clean (No Stay)',
                khatauni_no: 'KH-102-OD'
              };
              const d3 = {
                owner_name: 'S. Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                area_sqm: '1248',
                village: 'Chhatrapur',
                district: 'Ganjam',
                boundary_integrity: 'Verified (0% Encroachment)',
                gps_coordinates: '19.3541° N, 84.9872° E'
              };
              setDoc1Reg(d1);
              setDoc2Rev(d2);
              setDoc3Sur(d3);
              setSimulateDuplicateClaim(false);
              runComparison({ doc1: d1, doc2: d2, doc3: d3 }, false, true);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-amber-950/60 hover:bg-amber-900 border border-amber-500/50 text-amber-300 text-xs font-bold transition cursor-pointer flex items-center gap-1.5"
          >
            <span>⚠️ Name Alias Variation</span>
          </button>
          <button
            type="button"
            onClick={() => {
              const d1 = {
                owner_name: 'Sudrusti Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                khata_no: '102',
                area_sqm: '1800',
                village: 'Chhatrapur',
                district: 'Ganjam',
                registration_no: 'REG-2026-OD-8841',
                deed_date: '2026-08-15'
              };
              const d2 = {
                owner_name: 'Sudrusti Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                khata_no: '102',
                area_sqm: '1250',
                village: 'Chhatrapur',
                district: 'Ganjam',
                revenue_court_status: 'Clean (No Stay)',
                khatauni_no: 'KH-102-OD'
              };
              const d3 = {
                owner_name: 'Sudrusti Sethi',
                father_name: 'P. Sethi',
                survey_no: '45/0',
                area_sqm: '1200',
                village: 'Chhatrapur',
                district: 'Ganjam',
                boundary_integrity: '15% Boundary Encroachment Detected',
                gps_coordinates: '19.3541° N, 84.9872° E'
              };
              setDoc1Reg(d1);
              setDoc2Rev(d2);
              setDoc3Sur(d3);
              setSimulateDuplicateClaim(false);
              runComparison({ doc1: d1, doc2: d2, doc3: d3 }, false, true);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900 border border-rose-500/50 text-rose-300 text-xs font-bold transition cursor-pointer flex items-center gap-1.5"
          >
            <span>🚨 Area &amp; Boundary Dispute</span>
          </button>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto justify-end">
          {comparisonResult && (
            <div className="hidden sm:flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-950/90 border border-slate-700/80">
              <span className="text-[10px] uppercase font-bold text-slate-400">AI Confidence:</span>
              <span className={`text-sm font-black ${
                comparisonResult.overall_confidence >= 80 ? 'text-emerald-400' :
                comparisonResult.overall_confidence >= 60 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {comparisonResult.overall_confidence}%
              </span>
            </div>
          )}
          <button
            type="button"
            onClick={() => runComparison(null, null, true)}
            disabled={loading}
            className="w-full md:w-auto flex items-center justify-center gap-2.5 px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 hover:from-amber-400 hover:to-amber-300 text-slate-950 text-sm font-black shadow-lg shadow-amber-500/30 transition-all transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer disabled:opacity-50"
          >
            <Scale className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Evaluating Three-Way Records…' : '⚡ Evaluate & Analyse Evidence'}</span>
            <ArrowDown className="w-3.5 h-3.5 ml-0.5" />
          </button>
        </div>
      </div>

      {/* Feature 7 & 8: Three-Way AI Comparison Matrix & Ownership Confidence Engine */}
      {comparisonResult && (
        <div ref={resultsRef} className="glass-panel rounded-2xl p-5 border border-slate-800 bg-slate-900/80 space-y-5 animate-fade-in scroll-mt-6">
          {justEvaluated && (
            <div className="flex items-center justify-between p-2.5 px-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs font-bold animate-pulse">
              <span className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>3-Way Matrix &amp; Ownership Confidence Re-Evaluated with Updated Inputs</span>
              </span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                Live Analysis Clean
              </span>
            </div>
          )}

          {/* Ownership Confidence Header Gauge */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-200">
                  AI Ownership Confidence Assessment
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-xl">
                {comparisonResult.legal_position}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <span className="text-2xl font-black text-amber-400">
                  {comparisonResult.overall_confidence}%
                </span>
                <span className="block text-[10px] text-slate-400 font-semibold uppercase">
                  Confidence Score
                </span>
              </div>
              <div className="h-10 w-px bg-slate-800 hidden sm:block"></div>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700">
                  <span className="block text-amber-300 font-bold">{comparisonResult.registration_match}%</span>
                  <span className="text-[9px] text-slate-400">Deed (35%)</span>
                </div>
                <div className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700">
                  <span className="block text-cyan-300 font-bold">{comparisonResult.revenue_match}%</span>
                  <span className="text-[9px] text-slate-400">RoR (25%)</span>
                </div>
                <div className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700">
                  <span className="block text-emerald-300 font-bold">{comparisonResult.survey_match}%</span>
                  <span className="text-[9px] text-slate-400">Survey (25%)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Color-Coded Comparison Table (Feature 7) */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider bg-slate-950/60">
                  <th className="py-2.5 px-3">Field</th>
                  <th className="py-2.5 px-3 text-amber-300">1. Registration Deed</th>
                  <th className="py-2.5 px-3 text-cyan-300">2. Revenue RoR</th>
                  <th className="py-2.5 px-3 text-emerald-300">3. Cadastral Survey</th>
                  <th className="py-2.5 px-3 text-right">AI Match Alignment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {comparisonResult.comparison_matrix?.map((row, i) => {
                  const isGreen = row.status === 'EXACT_MATCH';
                  const isYellow = row.status === 'MINOR_MISMATCH';
                  return (
                    <tr key={i} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 font-bold text-slate-300">{row.label}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-mono">{row.registration}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-mono">{row.revenue}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-mono">{row.survey}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            isGreen
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : isYellow
                              ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {row.match_pct}% · {row.status.replace('_', ' ')}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Feature 14: Officer Decision Support & Recommendation Card */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-400">
                AI Recommendation for Revenue Officer
              </span>
              <p className="text-xs text-slate-200 font-semibold mt-0.5">
                {comparisonResult.recommendation}
              </p>
              <div className="mt-2 space-y-1">
                {comparisonResult.evidence_points?.map((pt, idx) => (
                  <p key={idx} className="text-[11px] text-slate-400 flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-emerald-400 shrink-0" />
                    <span>{pt}</span>
                  </p>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-2 shrink-0 md:w-64">
              <label className="text-[10px] text-slate-400 font-semibold">Officer Endorsement Remarks</label>
              <textarea
                value={officerNotes}
                onChange={(e) => setOfficerNotes(e.target.value)}
                rows={2}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 focus:border-amber-500 focus:outline-none"
              />
              <button
                onClick={handleDownloadPdf}
                disabled={generatingPdf}
                className="flex items-center justify-center gap-2 w-full py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black transition cursor-pointer shadow-md"
              >
                <FileCheck className="w-3.5 h-3.5" />
                <span>Issue Section 65B Evidence PDF</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
