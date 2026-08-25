import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Tooltip } from 'react-leaflet';
import { ShieldAlert, AlertCircle, CheckCircle, Scale, ArrowRight, Activity, MapPin, Sliders, Lock } from 'lucide-react';

export default function MapViewer({ parcelsData, selectedParcel, setSelectedParcel, onSelectTab, selectedRole }) {
  const [riskEnsemble, setRiskEnsemble] = useState(null);
  const [loadingRisk, setLoadingRisk] = useState(false);

  // Center around Shamshabad Mandal, Rangareddy District, Telangana (17.258, 78.434)
  const mapCenter = [17.258, 78.434];

  useEffect(() => {
    if (selectedParcel?.properties?.parcel_id) {
      fetchRiskDetails(selectedParcel.properties.parcel_id);
    }
  }, [selectedParcel]);

  const fetchRiskDetails = async (parcelId) => {
    setLoadingRisk(true);
    try {
      const res = await fetch(`/api/risk-score/${parcelId}`);
      if (res.ok) {
        const data = await res.json();
        setRiskEnsemble(data);
      }
    } catch (err) {
      console.error("Failed to fetch risk score", err);
    } finally {
      setLoadingRisk(false);
    }
  };

  const getParcelStyle = (feature) => {
    const props = feature.properties;
    const pid = props.parcel_id;
    const isAnomalous = props.is_anomalous;
    const isSelected = selectedParcel?.properties?.parcel_id === pid;

    let color = "#10b981"; // Green
    let fillColor = "#10b981";
    let fillOpacity = 0.35;

    if (pid === "P-105" || pid === "P-135" || pid === "P-108" || isAnomalous) {
      color = "#f43f5e"; // Red
      fillColor = "#f43f5e";
      fillOpacity = 0.55;
    } else if (pid === "P-112" || pid === "P-118" || props.revenue_court_status !== "Clean") {
      color = "#f59e0b"; // Yellow
      fillColor = "#f59e0b";
      fillOpacity = 0.45;
    }

    if (isSelected) {
      return {
        color: "#ffffff",
        weight: 3.5,
        fillColor: fillColor,
        fillOpacity: 0.75,
        dashArray: ""
      };
    }

    return {
      color: color,
      weight: 2,
      fillColor: fillColor,
      fillOpacity: fillOpacity
    };
  };

  const onEachFeature = (feature, layer) => {
    layer.on({
      click: () => {
        setSelectedParcel(feature);
      }
    });
  };

  // DPDP Act 2023 Data Minimization: Mask owner name for Citizen view
  const displayOwnerName = (name) => {
    if (selectedRole === 'Citizen' && name) {
      const parts = name.split(' ');
      return parts.length > 1 ? `${parts[0]} X. (Masked per DPDP Act)` : 'Pattadar (Masked per DPDP Act)';
    }
    return name;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">
      {/* Map Container */}
      <div className="lg:col-span-2 glass-panel rounded-2xl overflow-hidden border border-slate-800 relative flex flex-col">
        {/* Map Header Overlay */}
        <div className="absolute top-4 left-4 z-[400] glass-panel px-3.5 py-2 rounded-xl border border-slate-700/80 shadow-xl flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
          <div>
            <h3 className="text-xs font-bold text-slate-100">Shamshabad Cadastral Spatial Map</h3>
            <p className="text-[10px] text-slate-400">Telangana Dharani Layer • In-Memory GeoPandas/Shapely Spatial Engine</p>
          </div>
        </div>

        {/* Risk Legend Overlay */}
        <div className="absolute bottom-4 left-4 z-[400] glass-panel px-3 py-2 rounded-xl border border-slate-700/80 shadow-xl flex items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-500"></span>
            <span className="text-slate-300">Clean / Verified</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-amber-500"></span>
            <span className="text-slate-300">Medium Risk</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-rose-500"></span>
            <span className="text-slate-300">High Risk Flagged</span>
          </div>
        </div>

        {parcelsData && parcelsData.features ? (
          <MapContainer
            center={mapCenter}
            zoom={16}
            style={{ width: '100%', height: '100%' }}
            zoomControl={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            <GeoJSON
              key={JSON.stringify(parcelsData)}
              data={parcelsData}
              style={getParcelStyle}
              onEachFeature={onEachFeature}
            />
          </MapContainer>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
            Loading cadastral parcels...
          </div>
        )}
      </div>

      {/* Side Panel: Selected Parcel Details & Risk Explanation */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between overflow-y-auto">
        {selectedParcel ? (
          <div className="space-y-4">
            {/* Header: Parcel ID & Risk Badge */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                  {selectedParcel.properties.village || 'Shamshabad'}, Telangana
                </span>
                <h2 className="text-xl font-extrabold text-slate-100 mt-0.5">
                  Parcel {selectedParcel.properties.parcel_id}
                </h2>
                <p className="text-xs text-slate-400">
                  Survey No. {selectedParcel.properties.survey_no} • Khatian {selectedParcel.properties.khatian_no}
                </p>
              </div>

              {riskEnsemble && (
                <div
                  className={`px-3 py-1.5 rounded-xl border text-center font-bold text-xs ${
                    riskEnsemble.ensemble_risk_level === 'RED'
                      ? 'bg-rose-500/15 border-rose-500/30 text-rose-400 glow-rose'
                      : riskEnsemble.ensemble_risk_level === 'YELLOW'
                      ? 'bg-amber-500/15 border-amber-500/30 text-amber-400 glow-amber'
                      : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400 glow-emerald'
                  }`}
                >
                  <div className="text-[10px] uppercase tracking-wider">Risk Score</div>
                  <div className="text-lg leading-tight">{riskEnsemble.ensemble_risk_score}</div>
                </div>
              )}
            </div>

            {/* Parcel Attributes Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase font-semibold">
                  <span>Pattadar / Owner</span>
                  {selectedRole === 'Citizen' && <Lock className="w-3 h-3 text-amber-400" />}
                </div>
                <p className="font-bold text-slate-200 text-sm mt-0.5">
                  {displayOwnerName(selectedParcel.properties.owner_name)}
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-semibold">Revenue Court Status</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Scale className="w-3.5 h-3.5 text-amber-400" />
                  <p className="font-bold text-amber-300">{selectedParcel.properties.revenue_court_status}</p>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-semibold">Dharani Claimed Extent</span>
                <p className="font-bold text-slate-200 mt-0.5">{selectedParcel.properties.claimed_area_sqm} sqm</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-semibold">GIS Actual Extent</span>
                <p className="font-bold text-slate-200 mt-0.5">{selectedParcel.properties.actual_area_sqm} sqm</p>
              </div>
            </div>

            {/* Deterministic Engine 5 Weight Breakdown */}
            {riskEnsemble && (
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 text-[11px] space-y-1.5">
                <div className="flex items-center justify-between text-slate-400 font-semibold text-[10px] uppercase">
                  <span className="flex items-center gap-1">
                    <Sliders className="w-3 h-3 text-amber-400" />
                    Engine 5 Weight Matrix
                  </span>
                  <span className="text-amber-400">Fixed Deterministic</span>
                </div>
                <div className="grid grid-cols-4 gap-1 text-center font-mono">
                  <div className="bg-slate-900 p-1 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-400">GIS (E2)</div>
                    <div className="text-amber-300 font-bold">35%</div>
                  </div>
                  <div className="bg-slate-900 p-1 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-400">Title (E3)</div>
                    <div className="text-amber-300 font-bold">25%</div>
                  </div>
                  <div className="bg-slate-900 p-1 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-400">Sat (E4)</div>
                    <div className="text-amber-300 font-bold">25%</div>
                  </div>
                  <div className="bg-slate-900 p-1 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-400">OCR (E1)</div>
                    <div className="text-amber-300 font-bold">15%</div>
                  </div>
                </div>
              </div>
            )}

            {/* SHAP Explanation Panel */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-amber-400" />
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Engine 5 SHAP Feature Attribution</h4>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">XAI</span>
              </div>

              {loadingRisk ? (
                <div className="text-xs text-slate-400 py-2">Computing ensemble risk scores & SHAP feature values...</div>
              ) : riskEnsemble && riskEnsemble.top_explanations ? (
                <div className="space-y-2">
                  {riskEnsemble.top_explanations.map((exp, idx) => (
                    <div key={idx} className="p-2 rounded-lg bg-slate-950/70 border border-slate-800/80 flex items-start gap-2">
                      {riskEnsemble.ensemble_risk_level === 'RED' ? (
                        <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      ) : riskEnsemble.ensemble_risk_level === 'YELLOW' ? (
                        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      ) : (
                        <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      )}
                      <p className="text-xs text-slate-300 leading-relaxed font-medium">{exp}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">Select a parcel on the map to inspect feature explanations.</p>
              )}
            </div>

            {/* Navigation Actions */}
            <div className="space-y-2 pt-1">
              <button
                onClick={() => onSelectTab('ownership')}
                className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-semibold text-slate-200 border border-slate-700 transition"
              >
                <span>Inspect Ownership Timeline (Engine 3)</span>
                <ArrowRight className="w-4 h-4 text-amber-400" />
              </button>
              <button
                onClick={() => onSelectTab('satellite')}
                className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-semibold text-slate-200 border border-slate-700 transition"
              >
                <span>Check Satellite Land-Use Scene (Engine 4)</span>
                <ArrowRight className="w-4 h-4 text-amber-400" />
              </button>
              {selectedRole !== 'Citizen' && (
                <button
                  onClick={() => onSelectTab('review')}
                  className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold shadow-lg shadow-amber-500/20 transition"
                >
                  <span>Route to Revenue Officer Queue</span>
                  <ArrowRight className="w-4 h-4 text-slate-950" />
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <MapPin className="w-10 h-10 text-slate-600 mb-3 animate-bounce" />
            <h3 className="text-sm font-bold text-slate-200">No Parcel Selected</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-xs">
              Click on any colored parcel polygon on the GIS map to evaluate its topology, SHAP feature attribution, and ensemble risk score.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
