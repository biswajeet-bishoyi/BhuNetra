import React, { useState } from 'react';
import { ShieldCheck, UserCheck, Key, Lock, AlertCircle, CheckCircle, RefreshCw, X, FileText } from 'lucide-react';

export default function EKYCVerificationModal({ isOpen, onClose, parcelId, ownerName, onVerified }) {
  const [step, setStep] = useState('input'); // 'input' | 'otp' | 'success'
  const [aadhaarNumber, setAadhaarNumber] = useState('5489-2041-8921');
  const [mobileNumber, setMobileNumber] = useState('9876543210');
  const [otp, setOtp] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [consentData, setConsentData] = useState(null);
  const [agreedToDpdp, setAgreedToDpdp] = useState(true);

  if (!isOpen) return null;

  const handleGenerateOtp = async (e) => {
    e.preventDefault();
    if (!agreedToDpdp) {
      setError('Please agree to the DPDP Act 2023 consent terms.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/ekyc/generate-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aadhaar_number: aadhaarNumber,
          mobile_number: mobileNumber,
          purpose: `Land Record Title Verification for Parcel ${parcelId || 'P-OD-102'}`
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to generate OTP.');
      }
      const data = await res.json();
      setSessionId(data.data.session_id);
      setStep('otp');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/ekyc/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          otp: otp || '123456',
          claimed_name: ownerName || 'Sudrusti Sethi',
          parcel_id: parcelId || 'P-OD-102'
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'OTP verification failed.');
      }
      const data = await res.json();
      setConsentData(data.data);
      setStep('success');
      if (onVerified) onVerified(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/80">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">Aadhaar e-KYC & Landholder Consent</h3>
              <p className="text-[11px] text-slate-400 font-mono">
                UIDAI Direct Authentication · DPDP Act 2023 Compliant
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
        <div className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {step === 'input' && (
            <form onSubmit={handleGenerateOtp} className="space-y-4">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">Linked Parcel & Landholder</span>
                <div className="text-xs font-bold text-slate-200">
                  {ownerName || 'Sudrusti Sethi'} · <span className="text-amber-400 font-mono">Parcel {parcelId || 'P-OD-102'}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Aadhaar Number (12-Digits)
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={aadhaarNumber}
                    onChange={(e) => setAadhaarNumber(e.target.value)}
                    placeholder="XXXX-XXXX-XXXX"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 font-mono focus:outline-none focus:border-emerald-500 transition"
                    required
                  />
                  <Lock className="w-4 h-4 text-slate-500 absolute right-3.5 top-3" />
                </div>
                <span className="text-[10px] text-slate-500 font-mono mt-1 block">
                  🛡️ PII is masked & tokenized in accordance with Aadhaar Regulations 2016.
                </span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Registered Mobile Number
                </label>
                <input
                  type="text"
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  placeholder="+91-XXXXX-XXXXX"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 font-mono focus:outline-none focus:border-emerald-500 transition"
                  required
                />
              </div>

              {/* DPDP Act Consent Checkbox */}
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-start gap-2.5">
                <input
                  type="checkbox"
                  id="dpdp-consent"
                  checked={agreedToDpdp}
                  onChange={(e) => setAgreedToDpdp(e.target.checked)}
                  className="mt-0.5 rounded border-slate-700 text-emerald-500 focus:ring-emerald-500 cursor-pointer"
                />
                <label htmlFor="dpdp-consent" className="text-[11px] text-slate-300 cursor-pointer leading-tight">
                  I hereby give explicit consent under <strong>Section 6(1) of the Digital Personal Data Protection (DPDP) Act, 2023</strong> for my Aadhaar demographic details to be verified solely for the purpose of land record mutation and RoR issuance.
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-emerald-500/20 cursor-pointer disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
                <span>Send UIDAI e-KYC OTP</span>
              </button>
            </form>
          )}

          {step === 'otp' && (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300">
                OTP dispatched to your registered mobile ending in <strong>{mobileNumber.slice(-4)}</strong>. Valid for 5 minutes.
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Enter 6-Digit Aadhaar OTP
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="123456"
                  className="w-full bg-slate-900 border border-emerald-500/50 rounded-xl px-3.5 py-3 text-center text-xl tracking-widest text-emerald-400 font-mono focus:outline-none focus:border-emerald-400 transition"
                  autoFocus
                  required
                />
                <span className="text-[10px] text-slate-500 font-mono text-center block mt-1">
                  Demo Default OTP: <strong className="text-amber-400">123456</strong>
                </span>
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setStep('input')}
                  className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition cursor-pointer"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-2 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-emerald-500/20 cursor-pointer disabled:opacity-50"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                  <span>Verify e-KYC & Register Title</span>
                </button>
              </div>
            </form>
          )}

          {step === 'success' && consentData && (
            <div className="space-y-4">
              <div className="text-center py-2">
                <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center mx-auto mb-2">
                  <CheckCircle className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-slate-100">e-KYC Verification Successful</h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Demographic match confirmed against UIDAI Central Registry
                </p>
              </div>

              <div className="rounded-xl bg-slate-900 border border-slate-800 p-3 text-xs space-y-2 font-mono">
                <div className="flex justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400">Landholder Name:</span>
                  <span className="text-slate-100 font-bold">{consentData.demographic_profile.full_name}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400">Masked Aadhaar:</span>
                  <span className="text-slate-100">{consentData.masked_aadhaar}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400">Demographic Match:</span>
                  <span className="text-emerald-400 font-bold">{consentData.demographic_profile.name_match_confidence * 100}%</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400">Biometric Photo Score:</span>
                  <span className="text-emerald-400 font-bold">{consentData.demographic_profile.photo_match_score * 100}%</span>
                </div>
                <div className="flex justify-between pt-0.5">
                  <span className="text-slate-400">Sec 65B Digital Hash:</span>
                  <span className="text-cyan-300 truncate max-w-[180px]">{consentData.digital_signature_sec65b}</span>
                </div>
              </div>

              <button
                onClick={onClose}
                className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition cursor-pointer"
              >
                Complete & Return to Record
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
