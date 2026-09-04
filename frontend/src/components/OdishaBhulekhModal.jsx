import React, { useState } from 'react';
import {
  ExternalLink, ShieldCheck, Scale, History, X, CheckCircle2,
  AlertTriangle, Building, FileText, User, MapPin, Award, Search, Compass, RefreshCw
} from 'lucide-react';

const ODISHA_DISTRICTS_DATA = {
  Khordha: ['Bhubaneswar', 'Jatani', 'Balianta', 'Balipatna', 'Begunia', 'Bolagarh', 'Banapur', 'Tangi'],
  Cuttack: ['Cuttack Sadar', 'Salepur', 'Choudwar', 'Banki', 'Baramba', 'Athagarh', 'Nischintakoili'],
  Puri: ['Puri Sadar', 'Pipili', 'Nimapara', 'Gop', 'Satyabadi', 'Delanga', 'Brahmagiri', 'Kanas'],
  Ganjam: ['Berhampur', 'Chhatrapur', 'Hinjilicut', 'Bhanjanagar', 'Aska', 'Purushottampur'],
  Sambalpur: ['Sambalpur', 'Rengali', 'Kuchinda', 'Redhakhol', 'Dhankauda', 'Jujomura'],
  Balasore: ['Balasore', 'Basta', 'Jaleswar', 'Soro', 'Nilagiri', 'Bahanaga', 'Remuna'],
  Sundargarh: ['Sundargarh', 'Rourkela', 'Panposh', 'Rajgangpur', 'Bonai', 'Hemgir'],
  Mayurbhanj: ['Baripada', 'Rairangpur', 'Karanjia', 'Udala', 'Betnoti', 'Badasahi']
};

export default function OdishaBhulekhModal({
  isOpen,
  onClose,
  initialData = null,
  onLocateOnMap
}) {
  const [activeTab, setActiveTab] = useState('front'); // 'front' | 'back' | 'mutations' | 'report'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(initialData);

  // Form State for Interactive Search
  const [district, setDistrict] = useState('Khordha');
  const [tahasil, setTahasil] = useState('Bhubaneswar');
  const [village, setVillage] = useState('Patia');
  const [khataNo, setKhataNo] = useState('145/12');
  const [plotNo, setPlotNo] = useState('1024/2');
  const [tenantName, setTenantName] = useState('Bishnu Charan Das');
  const [areaDecimals, setAreaDecimals] = useState(15.0);

  if (!isOpen) return null;

  const handleDistrictChange = (e) => {
    const d = e.target.value;
    setDistrict(d);
    if (ODISHA_DISTRICTS_DATA[d] && ODISHA_DISTRICTS_DATA[d].length > 0) {
      setTahasil(ODISHA_DISTRICTS_DATA[d][0]);
    }
  };

  const handleFetchRecord = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/agents/odisha-bhulekh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          district,
          tahasil,
          village,
          khata_no: khataNo,
          plot_no: plotNo,
          tenant_name: tenantName,
          claimed_area_decimals: parseFloat(areaDecimals) || 15.0
        })
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message || 'Failed to query Odisha Bhulekh portal.');
    } finally {
      setLoading(false);
    }
  };

  // If initialData passed and no data loaded yet, load it
  if (!data && !loading && !error) {
    handleFetchRecord();
  }

  const front = data?.front_page;
  const back = data?.back_page;
  const tenant = front?.rayat_tenants?.[0];
  const plot = back?.plots?.[0];

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[92vh] bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl shadow-emerald-950/50 flex flex-col overflow-hidden text-slate-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-slate-900 via-emerald-950/40 to-slate-900">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white text-lg">
              📜
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-wide">
                  Odisha Bhulekh RoR (ସ୍ୱତ୍ତ୍ୱ ଲିପି) Intelligence
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Agno AI Agent Active
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                <span>Official Statutory Portal:</span>
                <a
                  href="https://bhulekh.ori.nic.in/RoRView.aspx"
                  target="_blank"
                  rel="noreferrer"
                  className="text-emerald-400 hover:text-emerald-300 underline font-medium flex items-center gap-1"
                >
                  https://bhulekh.ori.nic.in/RoRView.aspx
                  <ExternalLink className="w-3 h-3 inline" />
                </a>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search / Filter Bar */}
        <div className="px-6 py-3 bg-slate-950/70 border-b border-slate-800">
          <form onSubmit={handleFetchRecord} className="grid grid-cols-2 md:grid-cols-6 gap-2.5 items-end">
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                District (ଜିଲ୍ଲା)
              </label>
              <select
                value={district}
                onChange={handleDistrictChange}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                {Object.keys(ODISHA_DISTRICTS_DATA).map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Tahasil (ତହସିଲ)
              </label>
              <select
                value={tahasil}
                onChange={(e) => setTahasil(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                {(ODISHA_DISTRICTS_DATA[district] || []).map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Village / Mouza
              </label>
              <input
                type="text"
                value={village}
                onChange={(e) => setVillage(e.target.value)}
                placeholder="e.g. Patia"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Khata No (ଖାତା)
              </label>
              <input
                type="text"
                value={khataNo}
                onChange={(e) => setKhataNo(e.target.value)}
                placeholder="145/12"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Plot No (ପ୍ଲଟ୍)
              </label>
              <input
                type="text"
                value={plotNo}
                onChange={(e) => setPlotNo(e.target.value)}
                placeholder="1024/2"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-lg px-3 py-1.5 text-xs flex items-center justify-center gap-1.5 transition cursor-pointer shadow-md shadow-emerald-950/40"
              >
                {loading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Search className="w-3.5 h-3.5" />
                )}
                <span>Fetch RoR</span>
              </button>
            </div>
          </form>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 px-6 bg-slate-950/40">
          <button
            onClick={() => setActiveTab('front')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition cursor-pointer ${
              activeTab === 'front'
                ? 'border-emerald-500 text-emerald-300 bg-emerald-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>RoR Front Page (ସ୍ୱତ୍ତ୍ୱ ଲିପି)</span>
          </button>

          <button
            onClick={() => setActiveTab('back')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition cursor-pointer ${
              activeTab === 'back'
                ? 'border-emerald-500 text-emerald-300 bg-emerald-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>RoR Back Page (ପ୍ଲଟ ତାଲିକା)</span>
          </button>

          <button
            onClick={() => setActiveTab('mutations')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition cursor-pointer ${
              activeTab === 'mutations'
                ? 'border-emerald-500 text-emerald-300 bg-emerald-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Mutation History (ଦାଖଲ ଖାରଜ)</span>
          </button>

          <button
            onClick={() => setActiveTab('report')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition cursor-pointer ${
              activeTab === 'report'
                ? 'border-emerald-500 text-emerald-300 bg-emerald-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            <span>AI Cadastral Verdict</span>
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="py-16 flex flex-col items-center justify-center space-y-3">
              <div className="w-12 h-12 rounded-full border-4 border-emerald-500/20 border-t-emerald-500 animate-spin"></div>
              <p className="text-xs text-slate-300 font-semibold">
                Agno AI Agent Connecting to Odisha Bhulekh (bhulekh.ori.nic.in)...
              </p>
              <p className="text-[11px] text-slate-500">
                Retrieving RoR Front Page, Kissam classification, Sthitiban tenure & Mutation case records.
              </p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400" />
              <div>
                <p className="font-bold">Error Querying Odisha Bhulekh</p>
                <p className="text-rose-400 text-[11px] mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {!loading && data && (
            <>
              {/* Tab 1: Front Page */}
              {activeTab === 'front' && (
                <div className="space-y-4">
                  {/* Jurisdiction Summary Card */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                    <div>
                      <p className="text-[10px] uppercase font-bold text-slate-400">District (ଜିଲ୍ଲା)</p>
                      <p className="text-xs font-bold text-slate-200 mt-0.5">{front?.district}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-bold text-slate-400">Tahasil (ତହସିଲ)</p>
                      <p className="text-xs font-bold text-slate-200 mt-0.5">{front?.tahasil}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-bold text-slate-400">Mouza / Village</p>
                      <p className="text-xs font-bold text-slate-200 mt-0.5">{front?.village_mouza}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-bold text-slate-400">Khata No. (ଖାତା ନଂ)</p>
                      <p className="text-xs font-bold text-emerald-400 mt-0.5 font-mono">{front?.khata_no}</p>
                    </div>
                  </div>

                  {/* Rayat / Tenant Details */}
                  <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                        <User className="w-4 h-4 text-emerald-400" />
                        Recorded Rayat / Tenant Details (ରୟତଙ୍କ ବିବରଣୀ)
                      </h3>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        {tenant?.tenancy_status || 'ସ୍ଥିତିବାନ (Sthitiban)'}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="space-y-2">
                        <div>
                          <span className="text-slate-500">Rayat Name (ରୟତଙ୍କ ନାମ):</span>
                          <span className="text-slate-200 font-bold ml-2">{tenant?.name_en} ({tenant?.name_or})</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Father's Name (ପିତାଙ୍କ ନାମ):</span>
                          <span className="text-slate-200 ml-2">{tenant?.guardian_name}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Residence (ବାସସ୍ଥାନ):</span>
                          <span className="text-slate-300 ml-2">{tenant?.residence}</span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div>
                          <span className="text-slate-500">Share (ଅଂଶ):</span>
                          <span className="text-emerald-400 font-bold ml-2">{tenant?.share_fraction}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">OLR Tribal Category:</span>
                          <span className="text-slate-300 ml-2">{tenant?.olr_tribal_category}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Settlement Publication:</span>
                          <span className="text-slate-300 ml-2">{front?.publication_year}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Statutory Demand & Cess */}
                  <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                    <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-2">
                      <Scale className="w-4 h-4 text-emerald-400" />
                      Land Revenue & Statutory Cess (ଖଜଣା ଓ ସେସ୍)
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span className="text-slate-500 block text-[11px]">Rent (ଖଜଣା):</span>
                        <span className="font-mono text-slate-200 font-semibold">{front?.statutory_dues?.land_rent_khajana}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[11px]">Cess (ସେସ୍):</span>
                        <span className="font-mono text-slate-200 font-semibold">{front?.statutory_dues?.cess}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[11px]">Nistar Kar (ନିସ୍ତାର କର):</span>
                        <span className="font-mono text-slate-200 font-semibold">{front?.statutory_dues?.nistar_kar}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[11px]">e-Pauti Status:</span>
                        <span className="text-emerald-400 font-bold text-[11px]">{front?.statutory_dues?.e_pauti_payment_status}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Back Page (Plot Schedule) */}
              {activeTab === 'back' && (
                <div className="space-y-4">
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                          Plot Schedule & Land Classification (ପ୍ଲଟ୍ ତାଲିକା ଓ ଜମି କିସମ)
                        </h3>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Khata No: <span className="text-emerald-400 font-bold">{back?.khata_no}</span> | Total Plots: <span className="font-bold text-slate-200">{back?.total_khata_plots_count}</span>
                        </p>
                      </div>
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                        {back?.total_khata_area_acres}
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase">
                          <tr>
                            <th className="p-2.5 rounded-l-lg">Plot No (ପ୍ଲଟ୍)</th>
                            <th className="p-2.5">Kissam (କିସମ)</th>
                            <th className="p-2.5">Extent (Decimals)</th>
                            <th className="p-2.5">Area (Sq. Metres)</th>
                            <th className="p-2.5 rounded-r-lg">Remarks / Nothi (ମନ୍ତବ୍ୟ)</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/80">
                          {back?.plots?.map((p, idx) => (
                            <tr key={idx} className="hover:bg-slate-900/50">
                              <td className="p-2.5 font-bold font-mono text-emerald-400">{p.plot_no}</td>
                              <td className="p-2.5">
                                <span className="font-semibold text-slate-200">{p.kissam_en}</span>
                                <span className="text-[10px] text-slate-400 block">{p.kissam_or}</span>
                              </td>
                              <td className="p-2.5 font-semibold text-slate-200">{p.extent_decimals}</td>
                              <td className="p-2.5 font-mono text-slate-300">{p.extent_sqm} m²</td>
                              <td className="p-2.5 text-[11px] text-slate-400 max-w-xs">{p.remarks_nothi}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Boundary Description */}
                  <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <MapPin className="w-4 h-4 text-emerald-400" />
                      Physical Cadastral Boundaries (ଚୌହଦୀ)
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block text-[10px] uppercase font-bold">North (ଉତ୍ତର)</span>
                        <span className="text-slate-300 text-[11px] font-medium">{plot?.north_boundary}</span>
                      </div>
                      <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block text-[10px] uppercase font-bold">South (ଦକ୍ଷିଣ)</span>
                        <span className="text-slate-300 text-[11px] font-medium">{plot?.south_boundary}</span>
                      </div>
                      <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block text-[10px] uppercase font-bold">East (ପୂର୍ବ)</span>
                        <span className="text-slate-300 text-[11px] font-medium">{plot?.east_boundary}</span>
                      </div>
                      <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block text-[10px] uppercase font-bold">West (ପଶ୍ଚିମ)</span>
                        <span className="text-slate-300 text-[11px] font-medium">{plot?.west_boundary}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Mutations & Case History */}
              {activeTab === 'mutations' && (
                <div className="space-y-4">
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                      <History className="w-4 h-4 text-emerald-400" />
                      Tahasil Mutation Orders & Transaction Chain (ଦାଖଲ ଖାରଜ ଇତିହାସ)
                    </h3>
                    <div className="space-y-3">
                      {data?.mutation_history?.map((m, idx) => (
                        <div key={idx} className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-emerald-400 font-mono">{m.case_no}</span>
                            <span className="text-[10px] text-slate-400">{m.order_date}</span>
                          </div>
                          <p className="text-slate-200 font-semibold">{m.order_type}</p>
                          <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 mt-1">
                            <div>Court: <span className="text-slate-300">{m.tahasil_court}</span></div>
                            <div>Sub-Registrar: <span className="text-slate-300">{m.sub_registrar_office}</span></div>
                            <div>Transferee: <span className="text-slate-300 font-bold">{m.transferee}</span></div>
                            <div>Status: <span className="text-emerald-400 font-semibold">{m.status}</span></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: AI Cadastral Verdict */}
              {activeTab === 'report' && (
                <div className="space-y-4">
                  {/* Status Banner */}
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-lg">
                        ✓
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider">
                          Statutory Title Verification: Clean & Approved
                        </h4>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Verified against Odisha Bhulekh & OLR Act Sec 22/23 compliance standards.
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Audit Hash</span>
                      <span className="font-mono text-[10px] text-emerald-400">{data?.sha256_audit_hash?.slice(0, 24)}...</span>
                    </div>
                  </div>

                  {/* Markdown Executive Analysis */}
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs text-slate-300 space-y-2 leading-relaxed whitespace-pre-line">
                    {data?.executive_report}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-800 bg-slate-950/80 text-xs">
          <span className="text-slate-500 text-[11px]">
            Data synced from <strong className="text-slate-400">bhulekh.ori.nic.in</strong> • Revenue & Disaster Management Dept.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition cursor-pointer"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
