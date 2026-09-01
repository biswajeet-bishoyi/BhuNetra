/**
 * i18n.js — Simple multilingual dictionary for BhuNetra AI.
 *
 * Supports English (en) and Telugu (te). Use the <LangProvider> context
 * to access the current language + a setter. The choice is persisted in
 * localStorage so it survives reloads.
 */
import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const LANG_KEY = 'bhunetra_lang';

const DICTIONARY = {
  en: {
    // Tabs
    'tab.map': 'GIS Map',
    'tab.ocr': 'Registry OCR',
    'tab.ownership': 'Ownership Graph',
    'tab.satellite': 'Satellite Cross-Check',
    'tab.review': 'Officer Queue',
    'tab.revenue': 'Revenue Court',
    'tab.analytics': 'Executive Analytics',
    'tab.documents': 'Documents',
    'tab.mutations': 'Mutations',
    'tab.batch': 'Batch Process',
    // Buttons
    'btn.approve': 'Approve',
    'btn.reject': 'Reject',
    'btn.refresh': 'Refresh',
    'btn.search': 'Search parcel / survey / ULPIN',
    'btn.print': 'Print',
    'btn.download_pdf': 'Download PDF',
    'btn.sign_record': 'Sign & Record Approval Hash',
    'btn.simulate_alert': 'Simulate Send Alert',
    'btn.watch_demo': 'Watch 90-Second Demo',
    'btn.skip': 'Skip',
    // Risk levels
    'risk.green': 'Low Risk',
    'risk.yellow': 'Moderate Risk',
    'risk.red': 'High Risk',
    // Common
    'common.parcel': 'Parcel',
    'common.village': 'Village',
    'common.mandal': 'Mandal',
    'common.status': 'Status',
    'common.risk_score': 'Risk Score',
    'common.verified': 'Verified',
    'common.clean': 'Clean',
    'common.unknown': 'Unknown',
  },
  te: {
    'tab.map': 'భూమి వివరాలు',
    'tab.ocr': 'రిజిస్ట్రీ OCR',
    'tab.ownership': 'అమ్మకపు చరిత్ర',
    'tab.satellite': 'శాటిలైట్ ధృవీకరణ',
    'tab.review': 'అధికారి సమీక్ష',
    'tab.revenue': 'రెవెన్యూ కోర్ట్',
    'tab.analytics': 'విశ్లేషణలు',
    'tab.documents': 'పత్రాలు',
    'tab.mutations': 'మ్యుటేషన్లు',
    'tab.batch': 'బ్యాచ్ ప్రాసెసింగ్',
    'btn.approve': 'ఆమోదించు',
    'btn.reject': 'తిరస్కరించు',
    'btn.refresh': 'రిఫ్రెష్',
    'btn.search': 'పార్సెల్ / సర్వే / ULPIN శోధించండి',
    'btn.print': 'ముద్రణ',
    'btn.download_pdf': 'PDF డౌన్‌లోడ్',
    'btn.sign_record': 'ఆమోదం సంతకం',
    'btn.simulate_alert': 'హెచ్చరిక పంపు',
    'btn.watch_demo': '90 సెకన్ల డెమో చూడండి',
    'btn.skip': 'దాటవేయి',
    'risk.green': 'తక్కువ ప్రమాదం',
    'risk.yellow': 'మధ్యస్థ ప్రమాదం',
    'risk.red': 'అధిక ప్రమాదం',
    'common.parcel': 'పార్సెల్',
    'common.village': 'గ్రామం',
    'common.mandal': 'మండల్',
    'common.status': 'స్థితి',
    'common.risk_score': 'ప్రమాద స్కోర్',
    'common.verified': 'ధృవీకరించబడింది',
    'common.clean': 'శుభ్రం',
    'common.unknown': 'తెలియదు',
  },
};

const LangContext = createContext({ lang: 'en', setLang: () => {}, t: (k) => k });

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try { return localStorage.getItem(LANG_KEY) || 'en'; } catch { return 'en'; }
  });

  const setLang = useCallback((newLang) => {
    setLangState(newLang);
    try { localStorage.setItem(LANG_KEY, newLang); } catch {}
  }, []);

  const t = useCallback((key) => {
    return DICTIONARY[lang]?.[key] ?? DICTIONARY.en[key] ?? key;
  }, [lang]);

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return React.createElement(LangContext.Provider, { value }, children);
}

export function useLang() {
  return useContext(LangContext);
}
