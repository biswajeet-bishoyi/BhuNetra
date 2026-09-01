import React, { useState } from 'react';
import { MessageSquare, Smartphone, Bell, Check, CheckCheck, Send, X, ShieldAlert, AlertTriangle } from 'lucide-react';

export default function CitizenAlertModal({ isOpen, onClose, selectedParcelId = 'P-105' }) {
  const [activeChannel, setActiveChannel] = useState('whatsapp'); // 'whatsapp' | 'sms'
  const [selectedTemplate, setSelectedTemplate] = useState('overlap');
  const [sentAlerts, setSentAlerts] = useState([]);
  const [dispatching, setDispatching] = useState(false);

  if (!isOpen) return null;

  const templates = {
    overlap: {
      title: 'Boundary Conflict Detected',
      whatsapp: `🚨 *BHUNETRA LAND SECURITY ALERT*\n\nDear Pattadar,\n\nAn unauthorized boundary mutation on *Survey No. 101/A (Parcel ${selectedParcelId})*, Shamshabad has been *BLOCKED* by BhuNetra AI due to a *12.4% physical overlap* conflict with adjacent parcel P-106.\n\n• Risk Level: *HIGH (RED)*\n• Action: Mutation placed on administrative hold pending Tahsildar field survey.\n\n_Ref: IT Act 2000 §65B Digital Ledger_`,
      sms: `GOVT-TS-LAND: Alert! Mutation request on Sy.101/A (P-${selectedParcelId}) flagged by AI due to 12.4% boundary overlap. Mutation halted. Visit Tahsildar Shamshabad office with original passbook.`
    },
    rapid_resale: {
      title: 'Rapid Resale Velocity Flag',
      whatsapp: `⚠️ *BHUNETRA FRAUD ALERT — RAPID RESALE*\n\nDear Citizen,\n\nSuspicious transaction velocity recorded on *Parcel ${selectedParcelId}*: 4 transfers within 24 days with a 98% price spike.\n\n• Anti-Benami Advisory: Transaction flagged for Sub-Registrar review.\n\n_BhuNetra AI — Ministry of Rural Development_`,
      sms: `GOVT-TS-LAND: Warning! High-frequency transfer anomaly flagged on Parcel ${selectedParcelId}. Mutation locked pending Anti-Benami cell clearance.`
    },
    court_stay: {
      title: 'Revenue Court Stay Order',
      whatsapp: `⚖️ *REVENUE COURT LITIGATION NOTICE*\n\nNotice regarding *Parcel ${selectedParcelId}*:\n\nA *Stay Order* has been recorded under OS-412/2026 at Rangareddy Senior Civil Court. Any registry or conveyance deed will be void ab initio.\n\n_BhuNetra Automated Court Tracker_`,
      sms: `GOVT-TS-COURT: Stay Order active on Sy 101/A (P-${selectedParcelId}) per OS-412/2026. Sale/Pattadar transfer prohibited.`
    }
  };

  const handleDispatch = () => {
    setDispatching(true);
    setTimeout(() => {
      const newAlert = {
        id: Date.now(),
        channel: activeChannel,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: activeChannel === 'whatsapp' ? templates[selectedTemplate].whatsapp : templates[selectedTemplate].sms
      };
      setSentAlerts([newAlert, ...sentAlerts]);
      setDispatching(false);
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-2xl glass-panel rounded-2xl border border-slate-700/80 shadow-2xl p-6 bg-slate-900/95 text-slate-100 my-8">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
              <Bell className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">Citizen Fraud Alert Dispatch Simulator</h3>
              <p className="text-[11px] text-slate-400">Automated multi-channel push notification alerts on land risk anomalies</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Channel & Template Selectors */}
        <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Select Channel:</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setActiveChannel('whatsapp')}
                className={`py-2 px-3 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-1.5 ${
                  activeChannel === 'whatsapp'
                    ? 'bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-600/20'
                    : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>WhatsApp Alert</span>
              </button>
              <button
                onClick={() => setActiveChannel('sms')}
                className={`py-2 px-3 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-1.5 ${
                  activeChannel === 'sms'
                    ? 'bg-amber-500 text-slate-950 border-amber-500 shadow-lg shadow-amber-500/20'
                    : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                <span>Govt SMS Gateway</span>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Anomaly Trigger Scenario:</label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="w-full py-2 px-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:border-amber-500 focus:outline-none"
            >
              <option value="overlap">1. Boundary Overlap Anomaly (P-105)</option>
              <option value="rapid_resale">2. Rapid Resale Velocity (P-108)</option>
              <option value="court_stay">3. Revenue Court Stay Order (P-112)</option>
            </select>
          </div>
        </div>

        {/* Realistic Simulated Message Screen */}
        <div className="mt-4 p-4 rounded-2xl bg-slate-950 border border-slate-800">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-2 flex items-center justify-between">
            <span>Simulated {activeChannel === 'whatsapp' ? 'WhatsApp Business Screen' : 'Android SMS Screen'}</span>
            <span className="text-amber-400">Live Preview</span>
          </div>

          {activeChannel === 'whatsapp' ? (
            <div className="bg-[#0b141a] p-4 rounded-xl border border-slate-800 text-xs font-sans">
              <div className="flex items-center gap-2 pb-2.5 mb-2.5 border-b border-slate-800/80">
                <div className="w-7 h-7 rounded-full bg-emerald-700 flex items-center justify-center font-bold text-white text-xs">
                  BN
                </div>
                <div>
                  <div className="font-bold text-slate-200 text-xs flex items-center gap-1">
                    <span>BhuNetra Land Registry Verified</span>
                    <CheckCheck className="w-3 h-3 text-emerald-400" />
                  </div>
                  <div className="text-[10px] text-slate-400">Official Govt Land Alert Service</div>
                </div>
              </div>

              <div className="bg-[#1f2c34] p-3 rounded-xl text-slate-200 text-xs whitespace-pre-line leading-relaxed max-w-md shadow-md">
                {templates[selectedTemplate].whatsapp}
                <div className="text-right text-[9px] text-slate-400 mt-1 flex items-center justify-end gap-1">
                  <span>Just now</span>
                  <CheckCheck className="w-3 h-3 text-emerald-400" />
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-xs">
              <div className="text-[10px] font-bold text-slate-400 mb-1">From: VK-TSLAND (Govt Gateway)</div>
              <div className="bg-slate-800/90 p-3 rounded-xl text-slate-200 text-xs leading-relaxed">
                {templates[selectedTemplate].sms}
                <div className="text-right text-[9px] text-slate-400 mt-1">12:30 PM</div>
              </div>
            </div>
          )}
        </div>

        {/* Dispatch Trigger Button */}
        <div className="mt-4 flex items-center justify-between gap-3">
          <div className="text-xs text-slate-400">
            Simulates instant alert dispatch to Pattadar mobile (+91 98480 XXXXX)
          </div>
          <button
            onClick={handleDispatch}
            disabled={dispatching}
            className="py-2 px-4 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition flex items-center gap-1.5 shrink-0"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{dispatching ? 'Sending Alert...' : 'Simulate Send Alert'}</span>
          </button>
        </div>

      </div>
    </div>
  );
}
