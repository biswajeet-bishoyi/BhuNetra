import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, FileText, Camera, Eye, Cpu, Lock, Download, RefreshCw, X } from 'lucide-react';

export default function DocumentForensicsModal({ isOpen, onClose, docId, filename, parcelId }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ela'); // 'ela' | 'exif' | 'watermark'
  const [watermarking, setWatermarking] = useState(false);
  const [watermarkSuccess, setWatermarkSuccess] = useState(null);

  useEffect(() => {
    if (isOpen && docId) {
      fetchForensicReport();
    }
  }, [isOpen, docId]);

  const fetchForensicReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/documents/authenticate/${docId}`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
      const json = await res.json();
      setData(json.data);
    } catch (err) {
      setError(err.message || 'Failed to generate forensic report.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmbedWatermark = async () => {
    setWatermarking(true);
    setWatermarkSuccess(null);
    try {
      const res = await fetch(`/api/documents/${docId}/watermark`, { method: 'POST' });
      if (!res.ok) throw new Error('Watermark embedding failed.');
      const json = await res.json();
      setWatermarkSuccess(json.message);
      fetchForensicReport();
    } catch (err) {
      setError(err.message);
    } finally {
      setWatermarking(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[92vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-100">Document Forensic & Tamper Analysis</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                  DOC ID: #{docId}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {filename || 'Deed Scan Document'} · Target Parcel: <strong className="text-amber-300">{parcelId || 'P-OD-102'}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <p className="text-sm font-semibold text-slate-200">Executing Multi-Layer Forensic Engine…</p>
              <p className="text-xs text-slate-500 font-mono">Error Level Analysis (ELA) · EXIF Tag Scanning · LSB Integrity Check</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          ) : data ? (
            <>
              {/* Top Overview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {/* Tamper Risk Gauge */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
                  <span className="text-[11px] font-semibold text-slate-400">Tamper Probability</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className={`text-2xl font-extrabold font-mono ${
                      data.tamper_score < 30 ? 'text-emerald-400' : data.tamper_score < 60 ? 'text-amber-400' : 'text-rose-400'
                    }`}>
                      {data.tamper_score}%
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-500">
                      {data.authenticity_rating}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-2">
                    <div
                      className={`h-full ${data.tamper_score < 30 ? 'bg-emerald-400' : data.tamper_score < 60 ? 'bg-amber-400' : 'bg-rose-500'}`}
                      style={{ width: `${data.tamper_score}%` }}
                    />
                  </div>
                </div>

                {/* Provenance */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
                  <span className="text-[11px] font-semibold text-slate-400">Provenance Type</span>
                  <div className="mt-1">
                    <span className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                      <Camera className="w-4 h-4 text-cyan-400" />
                      {data.provenance_type.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono block mt-0.5">
                      {data.software || data.camera_model || 'Standard Flatbed Scanner'}
                    </span>
                  </div>
                </div>

                {/* Dimensions & DPI */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
                  <span className="text-[11px] font-semibold text-slate-400">Optical Resolution</span>
                  <div className="mt-1">
                    <span className="text-sm font-bold text-slate-100 font-mono">
                      {data.dimensions}
                    </span>
                    <span className="text-[10px] text-emerald-400 font-mono block mt-0.5">
                      {Array.isArray(data.dpi) ? `${data.dpi[0]} DPI` : '300 DPI (High Precision)'}
                    </span>
                  </div>
                </div>

                {/* Chain of Custody Watermark */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
                  <span className="text-[11px] font-semibold text-slate-400">Digital Watermark</span>
                  <div className="mt-1">
                    {data.chain_of_custody.has_watermark ? (
                      <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5" /> Embedded & Verified
                      </span>
                    ) : (
                      <span className="text-xs font-bold text-amber-400 flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> Unwatermarked
                      </span>
                    )}
                    <span className="text-[9px] text-slate-500 font-mono truncate block mt-0.5">
                      {data.chain_of_custody.watermark_payload || 'No LSB signature'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-slate-800 gap-4 text-xs font-bold">
                <button
                  onClick={() => setActiveTab('ela')}
                  className={`pb-2 transition border-b-2 cursor-pointer flex items-center gap-1.5 ${
                    activeTab === 'ela'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Error Level Analysis (ELA Heatmap)</span>
                </button>
                <button
                  onClick={() => setActiveTab('exif')}
                  className={`pb-2 transition border-b-2 cursor-pointer flex items-center gap-1.5 ${
                    activeTab === 'exif'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Cpu className="w-3.5 h-3.5" />
                  <span>EXIF & Provenance Inspector</span>
                </button>
                <button
                  onClick={() => setActiveTab('watermark')}
                  className={`pb-2 transition border-b-2 cursor-pointer flex items-center gap-1.5 ${
                    activeTab === 'watermark'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Lock className="w-3.5 h-3.5" />
                  <span>Chain-of-Custody LSB Watermark</span>
                </button>
              </div>

              {/* Tab 1: ELA Heatmap */}
              {activeTab === 'ela' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Original Scan */}
                    <div className="rounded-xl bg-slate-900 border border-slate-800 p-3 flex flex-col">
                      <span className="text-xs font-bold text-slate-300 mb-2">Original Document Scan</span>
                      <div className="relative flex-1 min-h-[260px] max-h-[300px] rounded-lg overflow-hidden bg-white/90 border border-slate-700 flex items-center justify-center">
                        <img
                          src={`/api/documents/${docId}/page/1`}
                          alt="Original deed"
                          className="max-h-[280px] w-auto object-contain"
                        />
                      </div>
                    </div>

                    {/* ELA Heatmap */}
                    <div className="rounded-xl bg-slate-900 border border-cyan-500/30 p-3 flex flex-col">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                          <span>🔥 ELA Difference Heatmap</span>
                          <span className="text-[10px] font-normal text-slate-400">(95% JPEG Resave Delta)</span>
                        </span>
                        <span className="text-[10px] font-mono text-cyan-400 font-bold bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800">
                          High Brightness = Modified
                        </span>
                      </div>
                      <div className="relative flex-1 min-h-[260px] max-h-[300px] rounded-lg overflow-hidden bg-slate-950 border border-cyan-500/40 flex items-center justify-center p-2">
                        <img
                          src={data.ela_heatmap_url}
                          alt="ELA Heatmap"
                          className="max-h-[280px] w-auto object-contain filter contrast-125"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
                    <h5 className="font-bold text-slate-100 flex items-center gap-1.5 mb-1">
                      <Shield className="w-4 h-4 text-cyan-400" />
                      Forensic Assessment & Interpretation
                    </h5>
                    <p className="text-slate-400 text-[11px] leading-relaxed">
                      Error Level Analysis (ELA) identifies areas in the deed that have different compression levels compared to the rest of the document.
                      Uniform error distribution indicates an untouched original scan, while isolated high-contrast bright spots indicate spliced text, forged survey numbers, or digitally pasted revenue seals.
                    </p>
                  </div>
                </div>
              )}

              {/* Tab 2: EXIF & Metadata Inspector */}
              {activeTab === 'exif' && (
                <div className="space-y-3">
                  <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-950 border-b border-slate-800 text-[10px] uppercase font-mono text-slate-400">
                        <tr>
                          <th className="p-2.5">Metadata Tag</th>
                          <th className="p-2.5">Extracted Value</th>
                          <th className="p-2.5">Forensic Classification</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
                        <tr>
                          <td className="p-2.5 text-slate-400">Camera / Scanner Hardware</td>
                          <td className="p-2.5 text-slate-200">{data.camera_make || 'Flatbed Optical Scanner'} {data.camera_model || ''}</td>
                          <td className="p-2.5 text-emerald-400">Standard Hardware</td>
                        </tr>
                        <tr>
                          <td className="p-2.5 text-slate-400">Software Signature</td>
                          <td className="p-2.5 text-slate-200">{data.software || 'None (Native Device Firmware)'}</td>
                          <td className="p-2.5">
                            {data.software ? (
                              <span className="text-amber-400">Digital Editing Trace</span>
                            ) : (
                              <span className="text-emerald-400">Unedited Firmware</span>
                            )}
                          </td>
                        </tr>
                        <tr>
                          <td className="p-2.5 text-slate-400">SHA-256 File Digest</td>
                          <td className="p-2.5 text-cyan-300 truncate max-w-[280px]">{data.sha256_hash}</td>
                          <td className="p-2.5 text-slate-400">Cryptographic Signature</td>
                        </tr>
                        <tr>
                          <td className="p-2.5 text-slate-400">Analysis Timestamp</td>
                          <td className="p-2.5 text-slate-300">{data.timestamp}</td>
                          <td className="p-2.5 text-slate-400">Audit Timestamp</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {data.tamper_indicators && data.tamper_indicators.length > 0 && (
                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-1">
                      <span className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5" /> Flagged Forensic Indicators ({data.tamper_indicators.length})
                      </span>
                      <ul className="list-disc list-inside text-[11px] text-amber-200 space-y-0.5">
                        {data.tamper_indicators.map((flag, idx) => (
                          <li key={idx}>{flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Digital LSB Watermark */}
              {activeTab === 'watermark' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                          <Lock className="w-4 h-4 text-cyan-400" />
                          Invisible LSB Cryptographic Chain-of-Custody Watermarking
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Invisibly embeds parcel ID, registry timestamp, and cryptographic hash into the least significant bits of the image pixels without degrading visual quality.
                        </p>
                      </div>
                      <button
                        onClick={handleEmbedWatermark}
                        disabled={watermarking}
                        className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
                      >
                        {watermarking ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />}
                        <span>Embed Custody Watermark</span>
                      </button>
                    </div>

                    {watermarkSuccess && (
                      <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        <span>{watermarkSuccess}</span>
                      </div>
                    )}

                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono space-y-1">
                      <div className="text-slate-400">Current Watermark Payload:</div>
                      <div className="text-cyan-300 break-all">
                        {data.chain_of_custody.watermark_payload || `BHUNETRA:DOC_${docId}:PARCEL_${parcelId || 'P-101'}:${data.sha256_hash.slice(0, 16)}`}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-mono">
            BhuNetra Forensic Engine · ISO 27037 Digital Evidence Standard
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition cursor-pointer"
          >
            Close Forensic Viewer
          </button>
        </div>
      </div>
    </div>
  );
}
