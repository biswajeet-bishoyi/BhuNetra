import React, { useState } from 'react';
import { Shield, Lock, Mail, Key, UserCheck, AlertCircle, X, Landmark, User, Sparkles, CheckCircle2 } from 'lucide-react';

export default function LoginModal({ isOpen, onClose, onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const json = await res.json();
      if (res.ok && json.success) {
        onLoginSuccess(json.user, json.token);
        onClose();
      } else {
        setError(json.detail || 'Invalid officer credentials. Please verify your security key.');
      }
    } catch (err) {
      setError('Connection error. Could not authenticate against revenue server.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAccount = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError('');
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-md glass-panel rounded-2xl border border-slate-700/80 shadow-2xl p-6 md:p-8 bg-slate-900/95 text-slate-100 my-8">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* National State Land Administration Header */}
        <div className="text-center space-y-2 pb-2">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-amber-500 to-amber-700 text-slate-950 flex items-center justify-center shadow-lg shadow-amber-500/20 border border-amber-400/30">
            <Shield className="w-8 h-8 stroke-[2.5]" />
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-widest text-amber-400 block font-mono">
              BHUNETRA AI • LAND VERIFICATION
            </span>
            <h2 className="text-xl font-black text-slate-100 tracking-tight mt-0.5">
              Official Portal Sign In
            </h2>
            <p className="text-xs text-slate-400">
              Access the Revenue Officer & Collector Decision Desk
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs rounded-xl font-semibold flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div className="space-y-1">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300">
              Officer Email / Identifier
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 font-semibold focus:border-amber-500 focus:outline-none placeholder:text-slate-600"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. collector@rangareddy.gov.in"
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300">
              Security Credential / Password
            </label>
            <div className="relative">
              <Key className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 font-semibold focus:border-amber-500 focus:outline-none placeholder:text-slate-600"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black text-xs uppercase tracking-wider shadow-lg shadow-amber-500/20 transition flex items-center justify-center gap-2"
          >
            <UserCheck className="w-4 h-4 stroke-[2.5]" />
            <span>{loading ? 'Authenticating Officer...' : 'Authorize & Sign In'}</span>
          </button>
        </form>

        {/* Instant Demo Account Quick-Fill Pills (Inspired by SmartHealth) */}
        <div className="space-y-2.5 pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-400" />
              Demo Fast-Fill Accounts
            </span>
            <span className="text-[10px] text-amber-400">1-Click Fill</span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => fillDemoAccount('collector@rangareddy.gov.in', 'Demo@1234')}
              className="px-2 py-2 rounded-xl bg-purple-500/15 hover:bg-purple-500/25 text-purple-300 border border-purple-500/30 text-[10px] font-bold transition text-center cursor-pointer flex flex-col items-center gap-1"
            >
              <Landmark className="w-3.5 h-3.5" />
              <span>Collector</span>
            </button>
            <button
              type="button"
              onClick={() => fillDemoAccount('tahsildar.shamshabad@telangana.gov.in', 'Demo@1234')}
              className="px-2 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 text-[10px] font-bold transition text-center cursor-pointer flex flex-col items-center gap-1"
            >
              <Shield className="w-3.5 h-3.5" />
              <span>Tahsildar</span>
            </button>
            <button
              type="button"
              onClick={() => fillDemoAccount('kalyan.reddy@citizen.in', 'Demo@1234')}
              className="px-2 py-2 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold transition text-center cursor-pointer flex flex-col items-center gap-1"
            >
              <User className="w-3.5 h-3.5" />
              <span>Citizen</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
