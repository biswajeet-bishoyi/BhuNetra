/**
 * DemoWalkthrough — 90-second guided tour of the BhuNetra AI demo.
 *
 * Each step waits 6-8 seconds and auto-navigates the UI, narrating what is
 * happening using the browser's Web Speech API (TTS). Officers can skip at any time.
 *
 * Steps:
 *  1. Map — selects P-105, highlights polygon
 *  2. GIS overlap result shown
 *  3. OCR tab — loads scan, runs extraction
 *  4. Ownership — rapid-resale pattern
 *  5. Satellite — land-use mismatch
 *  6. Risk Score — ensemble result
 *  7. Review Queue — officer approval simulation
 *  8. LandHealthCard — hash confirmation
 *  9. Citizen alert modal
 *  10. Reset to map view
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, SkipForward, X, Volume2 } from 'lucide-react';

const STEPS = [
  {
    id: 'map_intro',
    tab: 'map',
    highlight: 'parcel-p105',
    duration: 7000,
    narration: 'Welcome to BhuNetra AI — the AI verification layer for DILRMP land records. Clicking on parcel P-105, one of our flagged anomalies in Shamshabad Mandal.',
    narrationTe: 'భూనేత్ర AIకు స్వాగతం — DILRMP భూమి రికార్డుల కోసం AI ధృవీకరణ పొర. షాంషాబాద్ మండలంలోని మా ఫ్లాగ్ చేయబడిన అసాధారణాలలో P-105 పార్సెల్‌ను క్లిక్ చేయడం.',
  },
  {
    id: 'gis_overlap',
    tab: 'map',
    highlight: 'risk-panel',
    duration: 6000,
    narration: 'Engine Two, our GIS validation engine, detects a twelve-point-four percent boundary overlap with adjacent parcel P-106. This is flagged as RED — high risk.',
    narrationTe: 'మా GIS ధృవీకరణ ఇంజన్ పక్కపార్సెల్ P-106తో 12.4% బౌండరీ ఓవర్‌ల్యాప్‌ను గుర్తిస్తుంది. ఇది RED — అధిక ప్రమాదంగా ఫ్లాగ్ చేయబడింది.',
  },
  {
    id: 'ocr_tab',
    tab: 'ocr',
    highlight: 'ocr-panel',
    duration: 8000,
    narration: 'Engine One, the Registry OCR engine, reads the Dharani Record of Rights scan. It extracts all fields with per-field confidence scores. Low-confidence fields are flagged for officer review.',
    narrationTe: 'నమోదు OCR ఇంజన్ Dharani రికార్డ్ ఆఫ్ రైట్స్ స్కాన్‌ను చదువుతుంది. ప్రతి ఫీల్డ్‌కు విశ్వాస స్కోర్‌లతో అన్ని ఫీల్డ్‌లను ఎక్స్‌ట్రాక్ట్ చేస్తుంది.',
  },
  {
    id: 'ownership',
    tab: 'ownership',
    highlight: 'ownership-timeline',
    duration: 6000,
    narration: 'Engine Three, our Ownership Intelligence engine, detects a suspicious rapid resale pattern — four transfers within twenty-four days with a ninety-eight percent price spike. This is a Benami transaction risk signal.',
    narrationTe: 'మా ఓనర్‌షిప్ ఇంటెలిజెన్స్ ఇంజన్ అనుమానాస్పద రాపిడ్ రీసేల్ నమూనాను గుర్తిస్తుంది — 24 రోజులలో 4 బదలాయింపులు. ఇది బెనామీ లావాదేవీ ప్రమాద సంకేతం.',
  },
  {
    id: 'satellite',
    tab: 'satellite',
    highlight: 'satellite-panel',
    duration: 6000,
    narration: 'Engine Four, Satellite Verification, compares the registry land-use claim against Sentinel-2 satellite imagery. This parcel claims agricultural land, but the satellite shows a commercial warehouse built on it.',
    narrationTe: 'సైటలైట్ ధృవీకరణ, రిజిస్ట్రీ భూమి ఉపయోగంను Sentinel-2 ఉపగ్రహ చిత్రాలతో పోల్చుతుంది. ఈ పార్సెల్ వ్యవసాయ భూమిగా క్లెయిమ్ చేస్తుంది, కానీ ఉపగ్రహం వాణిజ్య గోడౌన్‌ను చూపిస్తుంది.',
  },
  {
    id: 'risk_score',
    tab: 'map',
    highlight: 'risk-panel',
    duration: 6000,
    narration: 'Engine Five, our Fraud Risk Ensemble, combines all four engine signals. With thirty-five percent GIS weight, twenty-five percent ownership, twenty-five percent satellite, and fifteen percent OCR, it computes a composite risk score of seventy-eight out of one hundred. This is RED — mutation hold recommended.',
    narrationTe: 'మా ఫ్రాడ్ రిస్క్ అంసెంబుల్ అన్ని నాలుగు ఇంజన్ సంకేతాలను కలుపుతుంది. 78 అవుట్ ఆఫ్ 100 కాంపోజిట్ రిస్క్ స్కోర్. ఇది RED — మ్యుటేషన్ హోల్డ్ సిఫార్సు చేయబడింది.',
  },
  {
    id: 'review_queue',
    tab: 'review',
    highlight: 'queue-panel',
    duration: 6000,
    narration: 'The Revenue Officer opens the Review Queue. The mandatory typed reason requirement ensures accountability. The officer can approve, override, or reject with documented justification.',
    narrationTe: 'రెవెన్యూ ఆఫీసర్ రివ్యూ క్యూను తెరుస్తారు. అవసరమైన టైప్ చేసిన కారణం అవసPersists. ఆఫీసర్ ఆమోదించవచ్చు, ఓవర్‌రైడ్ చేయవచ్చు లేదా తిరస్కరించవచ్చు.',
  },
  {
    id: 'health_card',
    tab: 'map',
    highlight: 'health-card',
    duration: 6000,
    narration: 'The Land Health Card displays the complete four-engine verification matrix. The SHA-256 hash generated here is admissible under IT Act 2000 Section 65B as electronic evidence.',
    narrationTe: 'ల్యాండ్ హెల్త్ కార్డ్ పూర్తి నలుగు-ఇంజన్ ధృవీకరణ మాతృకను ప్రదర్శిస్తుంది. SHA-256 హాష్ IT చట్టం 2000 సెక్షన్ 65B కింద ఎలక్ట్రానిక్ సాక్ష్యంగా అంగీకరించబడుతుంది.',
  },
  {
    id: 'citizen_alert',
    highlight: 'alert-modal',
    duration: 6000,
    narration: 'BhuNetra can send WhatsApp and SMS fraud alerts to citizens when anomalous mutations are detected on their land records. This is powered by real WhatsApp Business API integration.',
    narrationTe: 'భూమి రికార్డులపై అసాధారణ మ్యుటేషన్లు గుర్తించబడినప్పుడు BhuNetra పౌరులకు WhatsApp మరియు SMS మోసపు హెచ్చరికలను పంపవచ్చు.',
  },
  {
    id: 'done',
    tab: 'map',
    duration: 0,
    narration: 'That completes the ninety-second BhuNetra AI demo. All five verification engines work together to catch boundary overlaps, rapid resales, land-use mismatches, and deed discrepancies — before fraud happens.',
    narrationTe: '90 సెకన్ల BhuNetra AI డెమో పూర్తవుతుంది. అన్ని ఐదు ధృవీకరణ ఇంజన్లు కలిసి పనిచేస్తాయి.',
  },
];

export default function DemoWalkthrough({ onClose, onNavigate }) {
  const [currentStep, setCurrentStep] = useState(-1); // -1 = not started
  const [playing, setPlaying] = useState(false);
  const [language, setLanguage] = useState('en'); // 'en' | 'te'
  const timerRef = useRef(null);
  const utterRef = useRef(null);

  const stopNarration = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }, []);

  const speak = useCallback((text) => {
    if (!window.speechSynthesis || !text) return;
    stopNarration();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = language === 'te' ? 'te-IN' : 'en-IN';
    u.rate = 0.9;
    u.pitch = 1.0;
    utterRef.current = u;
    window.speechSynthesis.speak(u);
  }, [language, stopNarration]);

  const goToStep = useCallback((idx) => {
    if (idx < 0 || idx >= STEPS.length) {
      setPlaying(false);
      setCurrentStep(-1);
      onNavigate('map');
      return;
    }
    const step = STEPS[idx];
    if (step.tab) {
      onNavigate(step.tab);
    }
    speak(step.narration);
  }, [onNavigate, speak]);

  const advance = useCallback(() => {
    const next = currentStep + 1;
    if (next >= STEPS.length) {
      setPlaying(false);
      setCurrentStep(-1);
      stopNarration();
      onNavigate('map');
      return;
    }
    setCurrentStep(next);
    const step = STEPS[next];
    goToStep(next);
    if (step.duration > 0) {
      timerRef.current = setTimeout(() => {
        advance();
      }, step.duration);
    }
  }, [currentStep, goToStep, stopNarration, onNavigate]);

  const start = useCallback(() => {
    setCurrentStep(0);
    setPlaying(true);
    goToStep(0);
    const step = STEPS[0];
    if (step.duration > 0) {
      timerRef.current = setTimeout(() => {
        advance();
      }, step.duration);
    }
  }, [goToStep, advance]);

  const handleClose = useCallback(() => {
    stopNarration();
    clearTimeout(timerRef.current);
    setPlaying(false);
    setCurrentStep(-1);
    if (onClose) onClose();
  }, [stopNarration, onClose]);

  const skip = useCallback(() => {
    stopNarration();
    clearTimeout(timerRef.current);
    setPlaying(false);
    setCurrentStep(-1);
    onNavigate('map');
    if (onClose) onClose();
  }, [stopNarration, onNavigate, onClose]);

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'en' ? 'te' : 'en');
    if (currentStep >= 0) {
      const step = STEPS[currentStep];
      speak(language === 'en' ? step.narrationTe : step.narration);
    }
  };

  useEffect(() => {
    return () => {
      stopNarration();
      clearTimeout(timerRef.current);
    };
  }, [stopNarration]);

  const progress = currentStep < 0 ? 0 : Math.round(((currentStep + 1) / STEPS.length) * 100);
  const step = currentStep >= 0 ? STEPS[currentStep] : null;

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center pb-4 pointer-events-none">
      <div className={`glass-panel rounded-2xl border border-slate-700/80 shadow-2xl p-4 w-full max-w-lg mx-4 bg-slate-900/95 backdrop-blur-md space-y-3 pointer-events-auto`}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold text-amber-300">BhuNetra AI — 90-Second Demo</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleLanguage}
              className="px-2 py-1 rounded-lg bg-slate-800 text-[10px] font-bold text-slate-300 border border-slate-700 hover:bg-slate-700 cursor-pointer"
            >
              {language === 'en' ? 'EN' : 'TE'} / {language === 'en' ? 'TE' : 'EN'}
            </button>
            <button
              onClick={handleClose}
              title="Close Demo"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Progress bar */}
        {playing && (
          <div className="space-y-1.5">
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="h-full bg-amber-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span>Step {currentStep + 1}/{STEPS.length}</span>
              <span className="text-amber-400 font-semibold">{step?.id}</span>
            </div>
          </div>
        )}

        {/* Narration text */}
        {step && (
          <p className="text-xs text-slate-200 leading-relaxed italic min-h-[36px]">
            {language === 'te' ? step.narrationTe : step.narration}
          </p>
        )}

        {/* Controls */}
        <div className="flex items-center gap-2">
          {!playing ? (
            <button
              onClick={start}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Watch 90-Second Demo</span>
            </button>
          ) : (
            <>
              <div className="flex-1 flex items-center gap-2 py-2 px-3 rounded-xl bg-slate-800 text-xs text-slate-300">
                <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="font-semibold">Playing…</span>
              </div>
              <button
                onClick={skip}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
              >
                <SkipForward className="w-3.5 h-3.5" />
                <span>Skip</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
