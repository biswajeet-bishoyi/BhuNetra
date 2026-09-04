import React, { useEffect, useState, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  ShieldAlert, AlertCircle, CheckCircle, Scale, ArrowRight, Activity, MapPin,
  Sliders, Lock, FileText, Volume2, BellRing, Smartphone, MessageSquare, Sparkles,
  Compass, Layers, Maximize2
} from 'lucide-react';
import VoiceAssistant from './VoiceAssistant';
import LandHealthCard from './LandHealthCard';
import CitizenAlertModal from './CitizenAlertModal';

// Basemap style definitions for MapLibre GL JS
const BASEMAP_STYLES = {
  satellite: {
    version: 8,
    sources: {
      'esri-satellite': {
        type: 'raster',
        tiles: [
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        ],
        tileSize: 256,
        attribution: '&copy; Esri, Maxar, Earthstar Geographics'
      }
    },
    layers: [
      {
        id: 'satellite-tiles',
        type: 'raster',
        source: 'esri-satellite',
        minzoom: 0,
        maxzoom: 20
      }
    ]
  },
  streets: {
    version: 8,
    sources: {
      'osm-tiles': {
        type: 'raster',
        tiles: [
          'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
        ],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap contributors'
      }
    },
    layers: [
      {
        id: 'osm-tiles-layer',
        type: 'raster',
        source: 'osm-tiles',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  }
};

export default function MapViewer({
  parcelsData,
  selectedParcel,
  setSelectedParcel,
  onSelectTab,
  selectedRole
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const hoveredFeatureIdRef = useRef(null);

  const [mapLayer, setMapLayer] = useState('satellite'); // 'satellite' | 'streets'
  const [is3D, setIs3D] = useState(true);
  const [riskEnsemble, setRiskEnsemble] = useState(null);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [showHealthCard, setShowHealthCard] = useState(false);
  const [showFraudAlertModal, setShowFraudAlertModal] = useState(false);

  // Default Center: Shamshabad, Telangana (lng: 78.434, lat: 17.258)
  const defaultCenter = [78.434, 17.258];

  const toggle3D = () => {
    const map = mapRef.current;
    if (!map) return;
    const next3D = !is3D;
    setIs3D(next3D);
    if (next3D) {
      map.easeTo({
        pitch: 45,
        bearing: -15,
        duration: 800
      });
    } else {
      map.easeTo({
        pitch: 0,
        bearing: 0,
        duration: 800
      });
    }
  };

  // DPDP Act 2023 Data Minimization: Mask owner name for Citizen view
  const displayOwnerName = (name) => {
    if (selectedRole === 'Citizen' && name) {
      const parts = name.split(' ');
      return parts.length > 1 ? `${parts[0]} X. (Masked per DPDP Act)` : 'Pattadar (Masked per DPDP Act)';
    }
    return name;
  };

  // Helper to add parcels layers to MapLibre instance
  const addParcelLayers = (map, data) => {
    if (!data || !data.features) return;

    // Remove existing layers if present
    if (map.getLayer('parcels-label')) map.removeLayer('parcels-label');
    if (map.getLayer('parcels-stroke')) map.removeLayer('parcels-stroke');
    if (map.getLayer('parcels-fill')) map.removeLayer('parcels-fill');
    if (map.getSource('parcels-source')) map.removeSource('parcels-source');

    // Add GeoJSON Source
    map.addSource('parcels-source', {
      type: 'geojson',
      data: data,
      generateId: true
    });

    // 1. Cadastral Fill Layer with Dynamic Risk & Upload Styling
    map.addLayer({
      id: 'parcels-fill',
      type: 'fill',
      source: 'parcels-source',
      paint: {
        'fill-color': [
          'case',
          ['==', ['get', 'is_uploaded_plot'], true],
          '#06b6d4', // Cyan for uploaded deed plot
          ['==', ['get', 'parcel_id'], 'P-105'],
          '#f43f5e', // Red - Anomaly Flagged
          ['==', ['get', 'parcel_id'], 'P-135'],
          '#f43f5e',
          ['==', ['get', 'parcel_id'], 'P-108'],
          '#f43f5e',
          ['==', ['get', 'is_anomalous'], true],
          '#f43f5e',
          ['!=', ['get', 'revenue_court_status'], 'Clean'],
          '#f59e0b', // Amber - Court Litigation
          ['==', ['get', 'parcel_id'], 'P-112'],
          '#f59e0b',
          ['==', ['get', 'parcel_id'], 'P-118'],
          '#f59e0b',
          '#10b981'  // Emerald Green - Verified Clean
        ],
        'fill-opacity': [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.85,
          ['boolean', ['feature-state', 'selected'], false],
          0.90,
          0.50
        ]
      }
    });

    // 2. Cadastral Boundary Stroke Layer
    map.addLayer({
      id: 'parcels-stroke',
      type: 'line',
      source: 'parcels-source',
      paint: {
        'line-color': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          '#ffffff',
          ['==', ['get', 'is_uploaded_plot'], true],
          '#22d3ee',
          '#ffffff'
        ],
        'line-width': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          4,
          ['boolean', ['feature-state', 'hover'], false],
          3,
          1.8
        ]
      }
    });

    // 3. Cadastral Parcel Text Labels (Survey / Khasra / ID)
    map.addLayer({
      id: 'parcels-label',
      type: 'symbol',
      source: 'parcels-source',
      layout: {
        'text-field': [
          'coalesce',
          ['get', 'survey_no'],
          ['get', 'khasra_no'],
          ['get', 'parcel_id']
        ],
        'text-size': 12,
        'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
        'text-anchor': 'center',
        'text-allow-overlap': false
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': '#020617',
        'text-halo-width': 2
      }
    });

    // Mouse Interaction Events
    map.on('mousemove', 'parcels-fill', (e) => {
      if (e.features.length > 0) {
        if (hoveredFeatureIdRef.current !== null) {
          map.setFeatureState(
            { source: 'parcels-source', id: hoveredFeatureIdRef.current },
            { hover: false }
          );
        }
        hoveredFeatureIdRef.current = e.features[0].id;
        map.setFeatureState(
          { source: 'parcels-source', id: hoveredFeatureIdRef.current },
          { hover: true }
        );
        map.getCanvas().style.cursor = 'pointer';
      }
    });

    map.on('mouseleave', 'parcels-fill', () => {
      if (hoveredFeatureIdRef.current !== null) {
        map.setFeatureState(
          { source: 'parcels-source', id: hoveredFeatureIdRef.current },
          { hover: false }
        );
      }
      hoveredFeatureIdRef.current = null;
      map.getCanvas().style.cursor = '';
    });

    map.on('click', 'parcels-fill', (e) => {
      if (e.features.length > 0) {
        const feat = e.features[0];
        // Match with full GeoJSON feature from parcelsData
        const matched = data.features.find(
          (f) => f.properties?.parcel_id === feat.properties?.parcel_id
        ) || feat;
        setSelectedParcel(matched);
      }
    });
  };

  // Initialize MapLibre GL Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: BASEMAP_STYLES[mapLayer],
      center: defaultCenter,
      zoom: 16,
      pitch: 30, // 3D perspective pitch
      bearing: -5,
      attributionControl: false
    });

    // Add Map Navigation Controls (Zoom, 3D Pitch tilt, Compass)
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left');

    map.on('load', () => {
      if (parcelsData) {
        addParcelLayers(map, parcelsData);
      }
    });

    mapRef.current = map;

    return () => {
      map.remove();
    };
  }, []);

  // Update Style when Map Layer changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.setStyle(BASEMAP_STYLES[mapLayer]);
    map.once('style.load', () => {
      if (parcelsData) {
        addParcelLayers(map, parcelsData);
      }
    });
  }, [mapLayer]);

  // Update Data when parcelsData updates
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (parcelsData) {
      addParcelLayers(map, parcelsData);
    }
  }, [parcelsData]);

  // Handle Parcel Selection & Camera Fly-To Animation
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedParcel) return;

    try {
      let targetCenter = null;

      if (selectedParcel.properties?.centroid) {
        const c = selectedParcel.properties.centroid;
        targetCenter = [c[1], c[0]]; // [lng, lat]
      } else if (selectedParcel.geometry?.coordinates) {
        const coords = selectedParcel.geometry.coordinates[0];
        if (coords && coords.length > 0) {
          const lngs = coords.map((c) => c[0]);
          const lats = coords.map((c) => c[1]);
          const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
          const minLat = Math.min(...lats), maxLat = Math.max(...lats);
          targetCenter = [(minLng + maxLng) / 2, (minLat + maxLat) / 2];
        }
      }

      if (targetCenter) {
        map.flyTo({
          center: targetCenter,
          zoom: 17.5,
          pitch: 35,
          duration: 1200,
          essential: true
        });
      }

      // Update selected feature-state
      if (map.getSource('parcels-source') && parcelsData?.features) {
        parcelsData.features.forEach((f, idx) => {
          const isSel = f.properties?.parcel_id === selectedParcel.properties?.parcel_id;
          map.setFeatureState(
            { source: 'parcels-source', id: idx },
            { selected: isSel }
          );
        });
      }
    } catch (err) {
      console.error('Error centering MapLibre view:', err);
    }
  }, [selectedParcel]);

  // Fetch Risk Ensemble details on parcel selection
  useEffect(() => {
    if (selectedParcel?.properties?.parcel_id) {
      fetchRiskDetails(selectedParcel.properties.parcel_id);
    }
  }, [selectedParcel, selectedRole]);

  const fetchRiskDetails = async (parcelId) => {
    setLoadingRisk(true);
    try {
      const res = await fetch(
        `/api/risk-score/${parcelId}?role=${encodeURIComponent(selectedRole || 'Revenue Officer')}`
      );
      if (res.ok) {
        const data = await res.json();
        setRiskEnsemble(data);
      }
    } catch (err) {
      console.error('Failed to fetch risk score', err);
    } finally {
      setLoadingRisk(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">
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

      {/* WebGL Map Container */}
      <div className="lg:col-span-2 glass-panel rounded-2xl overflow-hidden border border-slate-800 relative flex flex-col">
        {/* Map Header Overlay */}
        <div className="absolute top-4 left-4 z-10 glass-panel px-3.5 py-2 rounded-xl border border-slate-700/80 shadow-2xl flex items-center gap-3 bg-slate-900/95 backdrop-blur-md">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shrink-0"></div>
          <div>
            <h3 className="text-xs font-bold text-slate-100 flex items-center gap-2">
              <span>
                {selectedParcel?.properties?.village || 'Bhubaneswar'} ({selectedParcel?.properties?.district || 'Khordha'}) Cadastral Map
              </span>
              {selectedParcel?.properties?.khasra_no && (
                <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] border border-amber-500/40">
                  Khasra {selectedParcel.properties.khasra_no}
                </span>
              )}
            </h3>
            <p className="text-[10px] text-slate-400">
              {selectedParcel?.properties?.cadastre_authority ||
                (selectedParcel?.properties?.state === 'Odisha'
                  ? 'Odisha Bhulekh Cadastre'
                  : selectedParcel?.properties?.state?.includes('Delhi')
                  ? 'Delhi DORIS Cadastre'
                  : 'Telangana Dharani Cadastre')}{' '}
              • MapLibre GL WebGL Vector Engine
            </p>
          </div>
        </div>

        {/* Map Layer Mode Switcher (Satellite vs Street) & 2D/3D Switcher */}
        <div className="absolute top-4 right-4 z-10 glass-panel p-1 rounded-xl border border-slate-700/80 shadow-2xl flex items-center gap-1.5 text-xs bg-slate-900/95 backdrop-blur-md">
          <button
            onClick={() => setMapLayer('satellite')}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 cursor-pointer ${
              mapLayer === 'satellite'
                ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <span>🛰️ Satellite</span>
          </button>
          <button
            onClick={() => setMapLayer('streets')}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 cursor-pointer ${
              mapLayer === 'streets'
                ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <span>🗺️ Streets</span>
          </button>
          <div className="h-4 w-[1px] bg-slate-700 mx-0.5" />
          <button
            onClick={toggle3D}
            title={is3D ? "Switch to Flat 2D Top-Down View" : "Switch to 3D Perspective Pitch View"}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-black transition flex items-center gap-1.5 cursor-pointer border ${
              is3D
                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-sm'
                : 'bg-slate-800 text-slate-300 border-slate-700 hover:text-white hover:bg-slate-700'
            }`}
          >
            <span>{is3D ? '📐 3D' : '🗺️ 2D'}</span>
          </button>
        </div>

        {/* Risk Legend Overlay */}
        <div className="absolute bottom-4 left-4 z-10 glass-panel px-3 py-2 rounded-xl border border-slate-700/80 shadow-2xl flex flex-wrap items-center gap-3 text-xs font-medium bg-slate-900/95 backdrop-blur-md">
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

        {/* MapLibre Canvas Container */}
        <div ref={mapContainerRef} className="w-full h-full min-h-[480px] flex-1" />
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
                  {selectedParcel.properties.village || 'Chandrasekharpur'},{' '}
                  {selectedParcel.properties.mandal || selectedParcel.properties.district || 'Khordha'},{' '}
                  {selectedParcel.properties.state || 'Odisha'}
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
                  {selectedParcel.properties.area_acres_printed
                    ? ` (${selectedParcel.properties.area_acres_printed})`
                    : ''}
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-semibold">GIS Actual Extent</span>
                <p className="font-bold text-slate-200 mt-0.5">
                  {selectedParcel.properties.actual_area_sqm} sqm
                </p>
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
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Engine 5 SHAP Feature Attribution
                  </h4>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">XAI</span>
              </div>

              {loadingRisk ? (
                <div className="text-xs text-slate-400 py-2">
                  Computing ensemble risk scores & SHAP feature values...
                </div>
              ) : riskEnsemble && riskEnsemble.top_explanations ? (
                <div className="space-y-2">
                  {riskEnsemble.top_explanations.map((exp, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg bg-slate-950/70 border border-slate-800/80 flex items-start gap-2"
                    >
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
                <p className="text-xs text-slate-400">
                  Select a parcel on the map to inspect feature explanations.
                </p>
              )}
            </div>

            {/* Action Buttons */}
            <div className="space-y-2 pt-1">
              <button
                onClick={() => setShowFraudAlertModal(true)}
                className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold shadow-md shadow-emerald-500/10 transition cursor-pointer"
              >
                <Smartphone className="w-4 h-4 text-emerald-400" />
                <span>
                  📱 Enable WhatsApp / SMS Fraud Alerts for Sy.{' '}
                  {selectedParcel.properties.survey_no}
                </span>
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
