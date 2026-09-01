import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StatusModal from './components/StatusModal';
import MapViewer from './components/MapViewer';
import OCRScanner from './components/OCRScanner';
import OwnershipTimeline from './components/OwnershipTimeline';
import SatelliteComparison from './components/SatelliteComparison';
import OfficerReviewQueue from './components/OfficerReviewQueue';
import RevenueCourtManager from './components/RevenueCourtManager';
import CollectorAnalytics from './components/CollectorAnalytics';
import CitizenAlertModal from './components/CitizenAlertModal';
import LoginModal from './components/LoginModal';
import DocumentsView from './components/DocumentsView';
import DemoWalkthrough from './components/DemoWalkthrough';
import { Shield, Scale, FileCheck, Lock } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('map');
  const [selectedRole, setSelectedRole] = useState('Revenue Officer');
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showFraudAlertModal, setShowFraudAlertModal] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  
  // Authenticated User State (Inspired by SmartHealth Auth Flow)
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('bhunetra_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [parcelsData, setParcelsData] = useState(null);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [showDemoWalkthrough, setShowDemoWalkthrough] = useState(false);

  useEffect(() => {
    fetchParcels();
  }, []);

  const fetchParcels = async () => {
    try {
      const res = await fetch('/api/gis-check/');
      if (res.ok) {
        const json = await res.json();
        setParcelsData(json);
        if (json.features && json.features.length > 0) {
          // Default select P-105 for demo anomaly showcase
          const p105 = json.features.find(f => f.properties.parcel_id === 'P-105') || json.features[0];
          setSelectedParcel(p105);
        }
      }
    } catch (err) {
      console.error("Failed to load parcels GIS data", err);
    }
  };

  const handleSelectParcelById = (pid) => {
    if (parcelsData && parcelsData.features) {
      const target = parcelsData.features.find(f => f.properties.parcel_id === pid);
      if (target) {
        setSelectedParcel(target);
      }
    }
    setActiveTab('map');
  };

  const handleRoleChange = (newRole) => {
    setSelectedRole(newRole);
    if (newRole === 'District Collector' && activeTab !== 'analytics') {
      setActiveTab('analytics');
    }
  };

  const handleLoginSuccess = (user, token) => {
    setCurrentUser(user);
    localStorage.setItem('bhunetra_user', JSON.stringify(user));
    localStorage.setItem('bhunetra_token', token);
    setSelectedRole(user.role);
    if (user.role === 'District Collector') {
      setActiveTab('analytics');
    } else if (user.role === 'Revenue Officer') {
      setActiveTab('review');
    } else {
      setActiveTab('map');
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('bhunetra_user');
    localStorage.removeItem('bhunetra_token');
    setSelectedRole('Citizen');
    setActiveTab('map');
    setShowLoginModal(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-amber-500 selection:text-slate-950">
      <div>
        {/* Navigation & Header */}
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedRole={selectedRole}
          setSelectedRole={handleRoleChange}
          showStatusModal={showStatusModal}
          setShowStatusModal={setShowStatusModal}
          onOpenAlertModal={() => setShowFraudAlertModal(true)}
          onStartDemo={() => setShowDemoWalkthrough(true)}
          onSelectParcel={handleSelectParcelById}
          currentUser={currentUser}
          onOpenLoginModal={() => setShowLoginModal(true)}
          onLogout={handleLogout}
        />

        {/* Status Tier Modal */}
        <StatusModal
          isOpen={showStatusModal}
          onClose={() => setShowStatusModal(false)}
        />

        {/* Official Portal Sign In Modal */}
        <LoginModal
          isOpen={showLoginModal}
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
        />

        {/* Citizen Fraud Alert Dispatch Simulator Modal */}
        <CitizenAlertModal
          isOpen={showFraudAlertModal}
          onClose={() => setShowFraudAlertModal(false)}
          selectedParcelId={selectedParcel?.properties?.parcel_id || 'P-105'}
        />

        {/* Guided Demo Walkthrough */}
        {showDemoWalkthrough && (
          <DemoWalkthrough
            onClose={() => setShowDemoWalkthrough(false)}
            onNavigate={(tab) => {
              setActiveTab(tab);
              if (tab === 'map' && parcelsData?.features) {
                const p105 = parcelsData.features.find(f => f.properties.parcel_id === 'P-105');
                if (p105) setSelectedParcel(p105);
              }
            }}
          />
        )}

        {/* Main Application Container */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          {activeTab === 'map' && (
            <MapViewer
              parcelsData={parcelsData}
              selectedParcel={selectedParcel}
              setSelectedParcel={setSelectedParcel}
              onSelectTab={setActiveTab}
              selectedRole={selectedRole}
            />
          )}

          {activeTab === 'ocr' && (
            <OCRScanner onSelectParcel={handleSelectParcelById} />
          )}

          {activeTab === 'ownership' && (
            <OwnershipTimeline
              selectedParcelId={selectedParcel?.properties?.parcel_id || 'P-108'}
              selectedRole={selectedRole}
            />
          )}

          {activeTab === 'satellite' && (
            <SatelliteComparison
              selectedParcelId={selectedParcel?.properties?.parcel_id || 'P-135'}
              selectedRole={selectedRole}
            />
          )}

          {activeTab === 'review' && (
            <OfficerReviewQueue onSelectParcel={handleSelectParcelById} selectedRole={selectedRole} />
          )}

          {activeTab === 'revenue' && (
            <RevenueCourtManager parcelsData={parcelsData} onRefresh={fetchParcels} />
          )}

          {activeTab === 'analytics' && (
            <CollectorAnalytics onSelectParcel={handleSelectParcelById} />
          )}

          {activeTab === 'documents' && (
            <DocumentsView onSelectParcel={handleSelectParcelById} />
          )}
        </main>
      </div>

      {/* Footer & Legal Compliance Grounding Note */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-4 px-4 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-amber-400" />
            <span className="font-bold text-slate-300">BhuNetra AI</span>
            <span>• SIH 2026 Problem Statement SIH26018 (Ministry of Rural Development)</span>
          </div>

          {/* Legal Compliance Grounding Pills */}
          <div className="flex flex-wrap items-center gap-3 text-[11px]">
            <span className="flex items-center gap-1 text-slate-400" title="Consent management and PII minimization for Citizen role">
              <Lock className="w-3 h-3 text-amber-400" />
              <span>DPDP Act 2023 Consent Minimization</span>
            </span>
            <span className="flex items-center gap-1 text-slate-400" title="Electronic audit trail timestamping & cryptographic hashing">
              <FileCheck className="w-3 h-3 text-emerald-400" />
              <span>IT Act 2000 Sec 65B Admissibility</span>
            </span>
            <span className="flex items-center gap-1 text-slate-400" title="Cryptographic proof validates digital records, not replacing registered deeds">
              <Scale className="w-3 h-3 text-amber-400" />
              <span>Registration Act 1908 Title Boundary</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
