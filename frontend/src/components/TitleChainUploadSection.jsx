import React, { useState } from 'react';
import {
  Upload,
  Layers,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  ArrowDown,
  Clock,
  FileText,
  ShieldCheck,
  ChevronRight,
  Info,
  Sparkles
} from 'lucide-react';

export default function TitleChainUploadSection({ onChainUpdated, currentExtractedData }) {
  const [includesAncestral, setIncludesAncestral] = useState(false);
  const [documents, setDocuments] = useState([
    {
      id: 1,
      doc_type: 'Grandfather Ancestral Deed / Partition',
      year: '1988',
      owner_name: 'Ramesh Mohanty',
      father_name: 'Late Jagannath Mohanty',
      survey_no: '45/0',
      khata_no: '102',
      area_sqm: '1250',
      registration_no: 'REG-1988-OD-104',
      is_ancestral: true,
      filename: '1988_Grandfather_Partition_Deed.pdf'
    },
    {
      id: 2,
      doc_type: 'Father Succession Mutation Order',
      year: '2004',
      owner_name: 'Suresh Mohanty',
      father_name: 'Ramesh Mohanty',
      survey_no: '45/0',
      khata_no: '102',
      area_sqm: '1250',
      registration_no: 'MUT-2004-GAN-88',
      is_ancestral: true,
      filename: '2004_Father_Mutation_Order.pdf'
    },
    {
      id: 3,
      doc_type: 'Current Registered Sale Deed',
      year: '2026',
      owner_name: 'Sudrusti Sethi',
      father_name: 'P. Sethi',
      survey_no: '45/0',
      khata_no: '102',
      area_sqm: '1250',
      registration_no: 'REG-2026-OD-8841',
      is_ancestral: false,
      filename: '2026_Current_Sale_Deed.pdf'
    }
  ]);

  const [reconstruction, setReconstruction] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [duplicateAlert, setDuplicateAlert] = useState(null);

  const handleAddDocument = () => {
    const newId = Date.now();
    setDocuments([
      ...documents,
      {
        id: newId,
        doc_type: 'Previous Transfer / Mutation',
        year: '2016',
        owner_name: '',
        father_name: '',
        survey_no: documents[0]?.survey_no || '45/0',
        khata_no: documents[0]?.khata_no || '102',
        area_sqm: documents[0]?.area_sqm || '1250',
        registration_no: `REG-2016-${Math.floor(100 + Math.random() * 900)}`,
        is_ancestral: true,
        filename: 'New_Ancestral_Record.pdf'
      }
    ]);
  };

  const handleRemoveDoc = (id) => {
    if (documents.length <= 1) return;
    setDocuments(documents.filter((d) => d.id !== id));
  };

  const handleUpdateDoc = (id, field, val) => {
    setDocuments(documents.map((d) => (d.id === id ? { ...d, [field]: val } : d)));
  };

  const handleReconstruct = async () => {
    setAnalyzing(true);
    setDuplicateAlert(null);
    try {
      const payload = {
        parcel_id: 'P-OD-102',
        has_ancestral_documents: includesAncestral,
        documents: documents.map((d) => ({
          owner_name: d.owner_name || 'Unknown',
          father_name: d.father_name || '',
          document_type: d.doc_type,
          deed_year: parseInt(d.year) || 2026,
          survey_no: d.survey_no || '45/0',
          khata_no: d.khata_no || '102',
          area_sqm: parseFloat(d.area_sqm) || 1250.0,
          registration_no: d.registration_no,
          is_ancestral: d.is_ancestral
        }))
      };

      const res = await fetch('/api/title-chain/upload-chain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const json = await res.json();
        setReconstruction(json.reconstruction);
        if (json.duplicate_claim_alert) {
          setDuplicateAlert(json.duplicate_claim_alert);
        }
        if (onChainUpdated) onChainUpdated(json);
      }
    } catch (e) {
      console.error('Reconstruction failed', e);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="mt-6 glass-panel rounded-2xl p-5 border border-slate-800 bg-slate-900/60 transition-all">
      {/* Feature 2: Ancestral Document Checkbox */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            id="ancestral-checkbox"
            checked={includesAncestral}
            onChange={(e) => {
              setIncludesAncestral(e.target.checked);
              if (e.target.checked && !reconstruction) {
                handleReconstruct();
              }
            }}
            className="mt-1 w-4 h-4 rounded text-amber-500 bg-slate-800 border-slate-700 focus:ring-amber-400 focus:ring-offset-slate-950 cursor-pointer"
          />
          <div>
            <label
              htmlFor="ancestral-checkbox"
              className="text-sm font-bold text-slate-100 cursor-pointer flex items-center gap-2"
            >
              Does this upload include ancestral or previous ownership documents?
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Multi-Doc Title Chain
              </span>
            </label>
            <p className="text-xs text-slate-400 mt-0.5">
              Enables chronological title-chain reconstruction, generational continuity verification, and duplicate claim screening.
            </p>
          </div>
        </div>

        {includesAncestral && (
          <button
            onClick={handleAddDocument}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold transition cursor-pointer shrink-0 self-start sm:self-auto"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Previous Deed</span>
          </button>
        )}
      </div>

      {/* Feature 1: Multi-Document Upload Section */}
      {includesAncestral && (
        <div className="mt-5 space-y-4 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {documents.map((doc, idx) => (
              <div
                key={doc.id}
                className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition relative group"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-amber-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Tier {idx + 1}: {doc.year}
                  </span>
                  {documents.length > 1 && (
                    <button
                      onClick={() => handleRemoveDoc(doc.id)}
                      className="text-slate-500 hover:text-rose-400 transition p-1 cursor-pointer"
                      title="Remove this document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div className="space-y-2 text-xs">
                  <div>
                    <label className="text-[10px] text-slate-400 block mb-0.5">Document Type</label>
                    <input
                      type="text"
                      value={doc.doc_type}
                      onChange={(e) => handleUpdateDoc(doc.id, 'doc_type', e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs focus:border-amber-500/60 focus:outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-0.5">Deed Year</label>
                      <input
                        type="text"
                        value={doc.year}
                        onChange={(e) => handleUpdateDoc(doc.id, 'year', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs focus:border-amber-500/60 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-0.5">Registration No.</label>
                      <input
                        type="text"
                        value={doc.registration_no}
                        onChange={(e) => handleUpdateDoc(doc.id, 'registration_no', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs focus:border-amber-500/60 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-400 block mb-0.5">Pattadar / Owner Name</label>
                    <input
                      type="text"
                      value={doc.owner_name}
                      onChange={(e) => handleUpdateDoc(doc.id, 'owner_name', e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-amber-300 font-bold text-xs focus:border-amber-500/60 focus:outline-none"
                      placeholder="e.g. Ramesh Mohanty"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-400 block mb-0.5">Father / Predecessor Name</label>
                    <input
                      type="text"
                      value={doc.father_name}
                      onChange={(e) => handleUpdateDoc(doc.id, 'father_name', e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-300 text-xs focus:border-amber-500/60 focus:outline-none"
                      placeholder="e.g. Late Jagannath Mohanty"
                    />
                  </div>

                  <div className="pt-1.5 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-800/80">
                    <span className="truncate max-w-[140px] text-slate-400">📄 {doc.filename}</span>
                    <span className="text-emerald-400 font-semibold">{doc.area_sqm} sq.m</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-400">
              {documents.length} deeds uploaded ({documents.filter((d) => d.is_ancestral).length} ancestral records)
            </span>
            <button
              onClick={handleReconstruct}
              disabled={analyzing}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs font-extrabold shadow-lg shadow-amber-500/20 transition cursor-pointer disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{analyzing ? 'Reconstructing Lineage…' : 'Reconstruct Title Chain'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Feature 3 & 11: Reconstructed Visual Timeline Flow */}
      {reconstruction && (
        <div className="mt-5 p-4 rounded-xl bg-slate-950 border border-slate-800 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-200">
                AI Title Chain Lineage Flowchart
              </h4>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase border ${
                  reconstruction.is_continuous
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                }`}
              >
                {reconstruction.status}
              </span>
              <span className="text-xs font-bold text-amber-300">
                {reconstruction.continuity_score}% Score
              </span>
            </div>
          </div>

          {/* Flowchart Nodes */}
          <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {reconstruction.chain?.map((node, i) => (
              <div key={i} className="relative group">
                <div className="absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full bg-slate-950 border-2 border-amber-400 group-hover:scale-110 transition"></div>
                <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-amber-400 text-xs font-mono">{node.year}</span>
                      <span className="text-slate-300 font-bold text-xs">{node.owner_name}</span>
                      {node.is_ancestral && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                          Ancestral
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {node.document_type} · Reg #{node.registration_no} · Sy. #{node.survey_no}
                      {node.father_name && ` (s/o ${node.father_name})`}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs font-semibold text-slate-300">{node.area_sqm} sq.m</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Explanations & Evidence Notes */}
          {reconstruction.reasons?.length > 0 && (
            <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1">
              {reconstruction.reasons.map((r, i) => (
                <p key={i} className="text-[11px] text-slate-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{r}</span>
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Feature 5 & 9: Duplicate Claim Warning Alert */}
      {duplicateAlert && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <h5 className="text-xs font-extrabold uppercase tracking-wider text-rose-300">
              High-Risk Duplicate Ownership Claim Detected ({duplicateAlert.conflict_score}% Conflict)
            </h5>
          </div>
          <div className="mt-2 text-xs space-y-1 text-slate-300">
            <p>
              <strong>Survey Number #{duplicateAlert.survey_no}</strong> already recorded under verified owner{' '}
              <span className="text-emerald-300 font-bold">{duplicateAlert.existing_owner}</span>.
            </p>
            <p>
              New claim uploaded by{' '}
              <span className="text-rose-300 font-bold">{duplicateAlert.new_claimant}</span> (Reg #{' '}
              {duplicateAlert.new_registration_no}).
            </p>
            <p className="text-[11px] text-rose-300/80 mt-1 italic">
              → This case has been automatically routed to the Revenue Officer review queue.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
