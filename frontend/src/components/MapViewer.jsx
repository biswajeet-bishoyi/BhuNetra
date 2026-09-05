import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Tooltip, Marker, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { ShieldAlert, AlertCircle, CheckCircle, Scale, ArrowRight, Activity, MapPin, Sliders, Lock, FileText, Volume2, BellRing, Smartphone, MessageSquare, Sparkles } from 'lucide-react';
import VoiceAssistant from './VoiceAssistant';
import LandHealthCard from './LandHealthCard';
import CitizenAlertModal from './CitizenAlertModal';

import L from 'leaflet';

function getParcelCenter(selectedParcel) {
  if (!selectedParcel) return null;
  if (selectedParcel.properties?.centroid) {
    const c = selectedParcel.properties.centroid;
    return [c[0], c[1]]; // [lat, lng]
  }
  if (selectedParcel.properties?.latitude && selectedParcel.properties?.longitude) {
    return [Number(selectedParcel.properties.latitude), Number(selectedParcel.properties.longitude)];
  }
  if (selectedParcel.geometry) {
    if (selectedParcel.geometry.type === 'Point') {
      return [selectedParcel.geometry.coordinates[1], selectedParcel.geometry.coordinates[0]];
    }
    const coords = selectedParcel.geometry.coordinates[0];
    if (coords && coords.length > 0) {
      const lats = coords.map(c => c[1]);
      const lngs = coords.map(c => c[0]);
      const minLat = Math.min(...lats), maxLat = Math.max(...lats);
      const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
      return [(minLat + maxLat) / 2, (minLng + maxLng) / 2];
    }
  }
  return null;
}

const createCadastralPinIcon = (label, isUploaded) => {
  const color = isUploaded ? '#06b6d4' : '#f59e0b';
  const shadowColor = isUploaded ? 'rgba(6, 182, 212, 0.7)' : 'rgba(245, 158, 11, 0.7)';
  return L.divIcon({
    className: 'cadastral-pin-marker',
    html: `
      <div style="position: relative; transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center; pointer-events: none;">
        <div style="
          background: rgba(15, 23, 42, 0.95);
          border: 2px solid ${color};
          color: #f8fafc;
          padding: 3px 8px;
          border-radius: 9999px;
          font-size: 11px;
          font-weight: 800;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          white-space: nowrap;
          box-shadow: 0 4px 14px ${shadowColor};
          display: flex;
          align-items: center;
          gap: 5px;
        ">
          <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${color}; box-shadow:0 0 8px ${color};"></span>
          <span>${label}</span>
        </div>
        <div style="
          width: 0;
          height: 0;
          border-left: 5px solid transparent;
          border-right: 5px solid transparent;
          border-top: 7px solid ${color};
          margin: 0 auto;
        "></div>
        <div style="
          width: 8px;
          height: 8px;
          background: ${color};
          border-radius: 50%;
          margin: -3px auto 0 auto;
          box-shadow: 0 0 10px ${color};
        "></div>
      </div>
    `,
    iconSize: [30, 42],
    iconAnchor: [15, 42]
  });
};

function MapRecenter({ selectedParcel }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    const center = getParcelCenter(selectedParcel);
    if (center) {
      try {
        map.flyTo(center, 18, { duration: 1.2 });
      } catch (e) {
        console.error("Map center error", e);
      }
    }
  }, [selectedParcel, map]);
  return null;
}

export default function MapViewer({ parcelsData, selectedParcel, setSelectedParcel, onSelectTab, selectedRole }) {
  const [internalParcels, setInternalParcels] = useState(null);
  const [riskEnsemble, setRiskEnsemble] = useState(null);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [showHealthCard, setShowHealthCard] = useState(false);
  const [showFraudAlertModal, setShowFraudAlertModal] = useState(false);

  // Center around Shamshabad Mandal, Rangareddy District, Telangana (17.258, 78.434)
  const mapCenter = [17.258, 78.434];

  // Self-heal / auto-fetch parcels if not yet available from parent
  useEffect(() => {
    if (!parcelsData || !parcelsData.features) {
      fetch('/api/gis-check/')
        .then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then(d => {
          if (d && d.features) {
            setInternalParcels(d);
            if (!selectedParcel && d.features.length > 0) {
              const p105 = d.features.find(f => f.properties?.parcel_id === 'P-105') || d.features[0];
              setSelectedParcel(p105);
            }
          }
        })
        .catch(err => console.error("Failed to load parcels GIS data", err));
    } else if (!selectedParcel && parcelsData?.features?.length > 0) {
      const p105 = parcelsData.features.find(f => f.properties?.parcel_id === 'P-105') || parcelsData.features[0];
      setSelectedParcel(p105);
    }
  }, [parcelsData]);

  const activeParcels = (parcelsData && parcelsData.features) ? parcelsData : internalParcels;

  useEffect(() => {
    if (selectedParcel?.properties?.parcel_id) {
      fetchRiskDetails(selectedParcel.properties.parcel_id);
    }
  }, [selectedParcel, selectedRole]);

  const fetchRiskDetails = async (parcelId) => {
    setLoadingRisk(true);
    try {
      const res = await fetch(`/api/risk-score/${parcelId}?role=${encodeURIComponent(selectedRole || 'Revenue Officer')}`);
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
    const props = feature.properties || {};
    const pid = props.parcel_id;
    const isAnomalous = props.is_anomalous;
    const isSelected = selectedParcel?.properties?.parcel_id === pid;
    const isUploaded = props.is_uploaded_plot;

    if (isUploaded) {
      return {
        color: "#06b6d4", // Electric cyan
        weight: isSelected ? 4.5 : 3,
        fillColor: "#06b6d4",
        fillOpacity: isSelected ? 0.85 : 0.65,
        dashArray: isSelected ? "" : "4, 4"
      };
    }

    let color = "#10b981"; // Green
    let fillColor = "#10b981";
    let fillOpacity = 0.40;

    if (pid === "P-105" || pid === "P-135" || pid === "P-108" || isAnomalous) {
      color = "#f43f5e"; // Red
      fillColor = "#f43f5e";
      fillOpacity = 0.60;
    } else if (pid === "P-112" || pid === "P-118" || props.revenue_court_status !== "Clean") {
      color = "#f59e0b"; // Yellow
      fillColor = "#f59e0b";
      fillOpacity = 0.50;
    }

    if (isSelected) {
      return {
        color: "#ffffff",
        weight: 3.5,
        fillColor: fillColor,
        fillOpacity: 0.80,
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

  const [mapLayer, setMapLayer] = useState('satellite'); // 'satellite' | 'streets'

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)] min-h-[600px]">
      {/* Land Health Card Modal */}
      <LandHealthCard
        parcelId={selectedParcel?.properties?.parcel_id || 'P-105'}
        selectedRole={selectedRole}
        isOpen={showHealthCard}
        onClose={() => setShowHealthCard(false)}
      />

      {/* Citizen Fraud Alert Dispatch Simulator Modal */}
      <CitizenAlertModal
        isOpen={showFraudAlertModal}
        onClose={() => setShowFraudAlertModal(false)}
        selectedParcelId={selectedParcel?.properties?.parcel_id || 'P-105'}
      />

      {/* Map Container */}
      <div className="lg:col-span-2 glass-panel rounded-2xl overflow-hidden border border-slate-800 relative flex flex-col h-full min-h-[550px] isolate z-0">
        {/* Map Header Overlay */}
        <div className="absolute top-4 left-4 z-[1000] glass-panel px-3.5 py-2 rounded-xl border border-slate-700/80 shadow-2xl flex items-center gap-3 bg-slate-900/95 backdrop-blur-md">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shrink-0"></div>
          <div>
            <h3 className="text-xs font-bold text-slate-100 flex items-center gap-2">
              <span>{selectedParcel?.properties?.village || 'Shamshabad'} ({selectedParcel?.properties?.district || 'Rangareddy'}) Cadastral Map</span>
              {selectedParcel?.properties?.survey_no && (
                <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] border border-amber-500/40">
                  Sy. {selectedParcel.properties.survey_no}
                </span>
              )}
            </h3>
            <p className="text-[10px] text-slate-400">
              {selectedParcel?.properties?.cadastre_authority || (selectedParcel?.properties?.state === 'Odisha' ? 'Odisha Bhulekh Cadastre' : (selectedParcel?.properties?.state?.includes('Delhi') ? 'Delhi DORIS Cadastre' : 'Telangana Dharani Cadastre'))} • Live GeoPandas / Shapely Spatial Index
            </p>
          </div>
        </div>

        {/* Map Layer Mode Switcher (Satellite vs Street) with z-[1000] */}
        <div className="absolute top-4 right-4 z-[1000] glass-panel p-1 rounded-xl border border-slate-700/80 shadow-2xl flex items-center gap-1.5 text-xs bg-slate-900/95 backdrop-blur-md">
          <button
            onClick={() => setMapLayer('satellite')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
              mapLayer === 'satellite'
                ? 'bg-amber-500 text-slate-950 shadow-md font-bold'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <span>🛰️ Satellite</span>
          </button>
          <button
            onClick={() => setMapLayer('streets')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
              mapLayer === 'streets'
                ? 'bg-amber-500 text-slate-950 shadow-md font-bold'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <span>🗺️ Streets</span>
          </button>
        </div>

        {/* Risk Legend Overlay */}
        <div className="absolute bottom-4 left-4 z-[1000] glass-panel px-3 py-2 rounded-xl border border-slate-700/80 shadow-2xl flex flex-wrap items-center gap-3 text-xs font-medium bg-slate-900/95 backdrop-blur-md">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-cyan-400 shadow-[0_0_8px_#06b6d4]"></span>
            <span className="text-cyan-300 font-bold">Uploaded Plot</span>
          </div>
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

        {activeParcels && activeParcels.features ? (
          <MapContainer
            center={mapCenter}
            zoom={16}
            style={{ width: '100%', height: '100%', minHeight: '550px' }}
            zoomControl={true}
          >
            <MapRecenter selectedParcel={selectedParcel} />
            {mapLayer === 'satellite' ? (
              <TileLayer
                attribution='&copy; <a href="https://www.esri.com/">Esri</a>, Maxar, Earthstar Geographics'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                maxZoom={19}
              />
            ) : (
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                maxZoom={19}
              />
            )}
            <GeoJSON
              key={`${JSON.stringify(activeParcels)}-${mapLayer}-${selectedParcel?.properties?.parcel_id}`}
              data={activeParcels}
              style={getParcelStyle}
              onEachFeature={onEachFeature}
            />
            {selectedParcel && (() => {
              const center = getParcelCenter(selectedParcel);
              if (!center) return null;
              const isUploaded = selectedParcel.properties?.is_uploaded_plot;
              const label = selectedParcel.properties?.survey_no 
                ? `Plot ${selectedParcel.properties.survey_no}` 
                : (selectedParcel.properties?.khasra_no 
                    ? `Khasra ${selectedParcel.properties.khasra_no}` 
                    : `Parcel ${selectedParcel.properties?.parcel_id}`);
              return (
                <Marker
                  key={`pin-${selectedParcel.properties?.parcel_id}-${center[0]}-${center[1]}`}
                  position={center}
                  icon={createCadastralPinIcon(label, isUploaded)}
                />
              );
            })()}
          </MapContainer>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm min-h-[500px]">
            Loading cadastral parcels...
          </div>
        )}
      </div>

      {/* Side Panel: Selected Parcel Details & Risk Explanation */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between overflow-y-auto space-y-4">
        {selectedParcel ? (
          <div className="space-y-4">
            {/* Header: Parcel ID & Risk Badge */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                {selectedParcel.properties.is_uploaded_plot && (
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-cyan-400" />
                      Uploaded Property Paper Plot
                    </span>
                  </div>
                )}
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                  {selectedParcel.properties.village || 'Chandrasekharpur'}, {selectedParcel.properties.mandal || selectedParcel.properties.district || 'Khordha'}, {selectedParcel.properties.state || 'Odisha'}
                </span>
                <h2 className="text-xl font-extrabold text-slate-100 mt-0.5">
                  Parcel {selectedParcel.properties.parcel_id}
                </h2>
                <div className="flex flex-wrap items-center gap-2 mt-1">
                  <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 font-mono text-xs font-bold border border-amber-500/40 shadow-sm">
                    Khasra No: {selectedParcel.properties.khasra_no || selectedParcel.properties.survey_no || 'N/A'}
                  </span>
                  {selectedParcel.properties.khatian_no && (
                    <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700">
                      Khata: {selectedParcel.properties.khatian_no}
                    </span>
                  )}
                </div>
                {selectedParcel.properties.cadastre_authority && (
                  <p className="text-[11px] text-emerald-400 font-medium mt-0.5 flex items-center gap-1">
                    <span>🏛️</span>
                    <span>{selectedParcel.properties.cadastre_authority}</span>
                  </p>
                )}
                {selectedParcel.properties.source_filename && (
                  <p className="text-[10px] text-cyan-400/90 mt-1 font-mono">
                    Doc: {selectedParcel.properties.source_filename}
                  </p>
                )}
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
                <span className="text-slate-400 text-[10px] uppercase font-semibold">Claimed Extent</span>
                <p className="font-bold text-slate-200 mt-0.5">
                  {selectedParcel.properties.claimed_area_sqm} sqm
                  {selectedParcel.properties.area_acres_printed ? ` (${selectedParcel.properties.area_acres_printed})` : ''}
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-semibold">GIS Actual Extent</span>
                <p className="font-bold text-slate-200 mt-0.5">{selectedParcel.properties.actual_area_sqm} sqm</p>
              </div>
            </div>

            {/* Vernacular Voice Assistant Component */}
            <VoiceAssistant
              parcelId={selectedParcel.properties.parcel_id}
              riskLevel={riskEnsemble?.ensemble_risk_level || 'GREEN'}
              riskScore={riskEnsemble?.ensemble_risk_score || 0.0}
              explanation={riskEnsemble?.top_explanations?.[0] || 'All spatial and title checks clean.'}
            />

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

            {/* Action Buttons */}
            <div className="space-y-2 pt-1">
              {/* Option A: Contextual Land Protection Fraud Alerts Button */}
              <button
                onClick={() => setShowFraudAlertModal(true)}
                className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold shadow-md shadow-emerald-500/10 transition cursor-pointer"
              >
                <Smartphone className="w-4 h-4 text-emerald-400" />
                <span>📱 Enable WhatsApp / SMS Fraud Alerts for Sy. {selectedParcel.properties.survey_no}</span>
              </button>

              <button
                onClick={() => setShowHealthCard(true)}
                className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-xs font-black text-slate-950 shadow-lg shadow-amber-500/20 transition cursor-pointer"
              >
                <FileText className="w-4 h-4 fill-current" />
                <span>Download / View Land Health Card (PDF)</span>
              </button>

              <button
                onClick={() => onSelectTab('ownership')}
                className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-semibold text-slate-200 border border-slate-700 transition cursor-pointer"
              >
                <span>Inspect Ownership Timeline (Engine 3)</span>
                <ArrowRight className="w-4 h-4 text-amber-400" />
              </button>

              <button
                onClick={() => onSelectTab('satellite')}
                className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-semibold text-slate-200 border border-slate-700 transition cursor-pointer"
              >
                <span>Check Satellite Land-Use Scene (Engine 4)</span>
                <ArrowRight className="w-4 h-4 text-amber-400" />
              </button>

              {selectedRole !== 'Citizen' && (
                <button
                  onClick={() => onSelectTab('review')}
                  className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-amber-300 text-xs font-bold border border-amber-500/30 transition cursor-pointer"
                >
                  <span>Route to Revenue Officer Queue</span>
                  <ArrowRight className="w-4 h-4 text-amber-400" />
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
