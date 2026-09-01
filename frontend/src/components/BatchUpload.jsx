/**
 * BatchUpload.jsx — Phase 3: Drag-and-drop multi-file batch processing.
 *
 * Officers drop multiple scanned documents onto the zone, set the
 * auto-extract toggle, and watch per-file progress live.
 */
import React, { useCallback, useRef, useState } from 'react';
import { Upload, X, Loader2, CheckCircle, AlertCircle, FileText, ArrowRight, Clock } from 'lucide-react';

const STATUS_STYLES = {
  queued:   'bg-slate-700/40 text-slate-300 border-slate-600/30',
  uploading:'bg-amber-500/15 text-amber-300 border-amber-500/30',
  extracted:'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  failed:   'bg-rose-500/15 text-rose-300 border-rose-500/30',
  done:     'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
};

const STATUS_ICONS = {
  queued:    Clock,
  uploading: Loader2,
  extracted: CheckCircle,
  failed:    AlertCircle,
  done:      CheckCircle,
};

function FileItem({ item }) {
  const Icon = STATUS_ICONS[item.status] || Clock;
  return (
    <div className="flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800">
      <div className="flex items-center gap-2.5 min-w-0">
        <FileText className="w-4 h-4 text-slate-400 shrink-0" />
        <div className="min-w-0">
          <p className="text-xs font-semibold text-slate-200 truncate max-w-[200px]">{item.filename}</p>
          {item.error && <p className="text-[10px] text-rose-300 mt-0.5">{item.error}</p>}
          {item.extraction_confidence != null && (
            <p className="text-[10px] text-slate-400 mt-0.5">
              Confidence: {(item.extraction_confidence * 100).toFixed(1)}% · {item.extraction_engine_tag}
              {item.low_confidence_fields?.length > 0 && (
                <span className="text-amber-400 ml-1">
                  · {item.low_confidence_fields.length} low-confidence field{item.low_confidence_fields.length !== 1 ? 's' : ''}
                </span>
              )}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {item.status === 'uploading' && (
          <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
        )}
        {item.status === 'extracted' && (
          <span className="text-[9px] font-bold text-emerald-400">EXTRACTED</span>
        )}
        {item.status === 'done' && (
          <span className="text-[9px] font-bold text-emerald-400">DONE</span>
        )}
        {item.status === 'failed' && (
          <span className="text-[9px] font-bold text-rose-400">FAILED</span>
        )}
        {item.status === 'queued' && (
          <span className="text-[9px] font-bold text-slate-400">QUEUED</span>
        )}
        <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${STATUS_STYLES[item.status] || STATUS_STYLES.queued}`}>
          {item.status.toUpperCase()}
        </span>
      </div>
    </div>
  );
}

export default function BatchUpload({ onUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [autoExtract, setAutoExtract] = useState(false);
  const [files, setFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [summary, setSummary] = useState(null);
  const inputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragging(false), []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = Array.from(e.dataTransfer.files);
    addFiles(dropped);
  }, []);

  const handleInputChange = (e) => {
    const selected = Array.from(e.target.files);
    addFiles(selected);
    e.target.value = '';
  };

  const addFiles = (newFiles) => {
    const items = newFiles.map(f => ({
      id: `${f.name}-${f.size}-${Date.now()}-${Math.random()}`,
      filename: f.name,
      size: f.size,
      file: f,
      status: 'queued',
      error: null,
      document_id: null,
      extraction_confidence: null,
      extraction_engine_tag: null,
      low_confidence_fields: null,
    }));
    setFiles(prev => [...prev, ...items]);
  };

  const removeFile = (id) => setFiles(prev => prev.filter(f => f.id !== id));

  const handleUpload = async () => {
    if (files.length === 0) return;
    setSubmitting(true);

    // Build multipart/form-data body
    const body = new FormData();
    files.forEach(f => body.append('files', f.file));
    if (autoExtract) body.append('extract', 'true');

    // Mark all as uploading
    setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' })));

    try {
      const res = await fetch('/api/documents/batch', { method: 'POST', body });

      if (!res.ok) {
        const err = await res.text();
        throw new Error(err || `Server error ${res.status}`);
      }

      const receipt = await res.json();

      // Update each file entry with server result
      setFiles(prev => prev.map(f => {
        const server = receipt.results?.find(r => r.filename === f.filename);
        if (!server) return { ...f, status: 'failed', error: 'No result from server' };
        return {
          ...f,
          status: server.error ? 'failed' : autoExtract ? 'extracted' : 'done',
          error: server.error || null,
          document_id: server.document_id,
          extraction_confidence: server.extraction_confidence,
          extraction_engine_tag: server.extraction_engine_tag,
          low_confidence_fields: server.low_confidence_fields,
        };
      }));

      setSummary(receipt);
    } catch (err) {
      setFiles(prev => prev.map(f => ({ ...f, status: 'failed', error: err.message })));
      setSummary({ total: files.length, succeeded: 0, failed: files.length, error: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const completedCount = files.filter(f => ['done', 'extracted', 'failed'].includes(f.status)).length;
  const allDone = completedCount === files.length && files.length > 0;
  const canUpload = files.length > 0 && !submitting;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Upload className="w-4 h-4 text-amber-400" />
              Batch Document Processing
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Drop multiple scanned land-record PDFs or images onto the zone below. Each file is
              registered and optionally run through Engine 1 OCR extraction. Up to 20 files per batch.
            </p>
          </div>
          {/* Summary */}
          {summary && (
            <div className="flex items-center gap-2 text-[11px] font-bold">
              <span className="px-2 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">
                {summary.succeeded} succeeded
              </span>
              {summary.failed > 0 && (
                <span className="px-2 py-1 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300">
                  {summary.failed} failed
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Drop zone + options */}
        <div className="space-y-3">
          {/* Drop zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition select-none ${
              dragging
                ? 'border-amber-400 bg-amber-500/10'
                : 'border-slate-700 hover:border-slate-600 bg-slate-900/50'
            }`}
          >
            <Upload className={`w-8 h-8 mx-auto mb-2 ${dragging ? 'text-amber-400' : 'text-slate-500'}`} />
            <p className="text-xs font-bold text-slate-200">
              {dragging ? 'Release to drop' : 'Drop files here or click to browse'}
            </p>
            <p className="text-[10px] text-slate-400 mt-1">
              PNG, JPG, PDF, TIF — max 12 MB each · up to 20 files
            </p>
            <input
              ref={inputRef}
              type="file"
              multiple
              accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp,.webp,.pdf"
              onChange={handleInputChange}
              className="hidden"
            />
          </div>

          {/* Options */}
          <div className="glass-panel rounded-xl border border-slate-800 p-4 space-y-3">
            <h3 className="text-xs font-bold text-slate-300">Processing Options</h3>

            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={autoExtract}
                onChange={e => setAutoExtract(e.target.checked)}
                className="mt-0.5 w-3.5 h-3.5 rounded accent-amber-500"
              />
              <div>
                <p className="text-xs font-semibold text-slate-200">Auto-extract on upload</p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Immediately run Engine 1 OCR on each file after registration.
                  Disabling uploads only (faster for large batches).
                </p>
              </div>
            </label>

            <button
              onClick={handleUpload}
              disabled={!canUpload}
              className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-slate-950 text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Processing {files.length} file{files.length !== 1 ? 's' : ''}…
                </>
              ) : allDone ? (
                <>
                  <ArrowRight className="w-3.5 h-3.5" />
                  Re-process
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5" />
                  Upload {files.length} File{files.length !== 1 ? 's' : ''}
                </>
              )}
            </button>

            {files.length > 0 && (
              <button
                onClick={() => { setFiles([]); setSummary(null); }}
                className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 cursor-pointer"
              >
                Clear All
              </button>
            )}
          </div>
        </div>

        {/* File list */}
        <div className="lg:col-span-2 glass-panel rounded-2xl border border-slate-800 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-slate-300">
              Files ({files.length})
            </h3>
            {files.length > 0 && (
              <div className="text-[10px] text-slate-400">
                {completedCount}/{files.length} complete
                {submitting && <span className="ml-1 text-amber-400">· processing…</span>}
              </div>
            )}
          </div>

          {files.length === 0 ? (
            <div className="text-xs text-slate-400 text-center py-12">
              <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              No files queued. Drag and drop or click the zone to add files.
            </div>
          ) : (
            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
              {files.map(f => (
                <div key={f.id} className="flex items-center gap-2">
                  <div className="flex-1">
                    <FileItem item={f} />
                  </div>
                  {!submitting && (
                    <button
                      onClick={() => removeFile(f.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-rose-300 hover:bg-rose-500/10 transition shrink-0 cursor-pointer"
                      title="Remove"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
