import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Globe, Play, Square, Sparkles } from 'lucide-react';

export default function VoiceAssistant({ parcelId = 'P-105', riskLevel = 'RED', riskScore = 74.8, explanation = 'Boundary overlap of 12.4% detected with adjacent parcel P-106.' }) {
  const [language, setLanguage] = useState('en');
  const [speaking, setSpeaking] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);

  useEffect(() => {
    const loadVoices = () => {
      if ('speechSynthesis' in window) {
        setAvailableVoices(window.speechSynthesis.getVoices());
      }
    };
    loadVoices();
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  const getAudioText = () => {
    if (language === 'te') {
      return {
        title: 'భూనేత్ర భూమి రికార్డు వివరాలు',
        text: `సర్వే నంబర్ ${parcelId} కు సంబంధించి ధరణి రికార్డులలో హై రిస్క్ గుర్తించబడింది. రిస్క్ స్కోరు ${riskScore}. ప్రక్కనే ఉన్న ప్లాటుతో సరిహద్దు వివాదం ఉన్నందున తహశీల్దార్ లేదా రెవెన్యూ అధికారి క్షేత్రస్థాయి పరిశీలన అవసరం.`,
        advice: 'రిజిస్ట్రేషన్ లేదా మ్యుటేషన్ చేయడానికి ముందు మండల రెవెన్యూ ఆఫీస్ లో సంప్రదించండి.'
      };
    } else if (language === 'hi') {
      return {
        title: 'भू-नेत्र भूमि सत्यापन विवरण',
        text: `पार्सल ${parcelId} के लिए उच्च जोखिम स्तर दर्ज किया गया है। जोखिम स्कोर ${riskScore} है। पड़ोसी भूखंड के साथ सीमा ओवरलैप पाया गया है। म्यूटेशन से पहले राजस्व अधिकारी का सत्यापन अनिवार्य है।`,
        advice: 'जमीन की रजिस्ट्री या नामांतरण से पहले तहसीलदार कार्यालय से संपर्क करें।'
      };
    } else {
      return {
        title: 'BhuNetra Land Health Advisory',
        text: `Land Parcel ${parcelId} has been flagged with ${riskLevel} risk level. Calculated risk score is ${riskScore} out of 100. ${explanation}. Physical verification by the Revenue Officer is required before mutation proceeds.`,
        advice: 'Consult the Tahsildar / Revenue Inspector desk for physical boundary resolution.'
      };
    }
  };

  const currentContent = getAudioText();

  const handleSpeak = () => {
    if (!('speechSynthesis' in window)) {
      alert("Text-to-speech is not supported in this browser.");
      return;
    }

    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(`${currentContent.title}. ${currentContent.text}. ${currentContent.advice}`);

    if (language === 'te') {
      utterance.lang = 'te-IN';
      const teVoice = availableVoices.find(v => v.lang.includes('te'));
      if (teVoice) utterance.voice = teVoice;
    } else if (language === 'hi') {
      utterance.lang = 'hi-IN';
      const hiVoice = availableVoices.find(v => v.lang.includes('hi'));
      if (hiVoice) utterance.voice = hiVoice;
    } else {
      utterance.lang = 'en-IN';
      const enVoice = availableVoices.find(v => v.lang.includes('en'));
      if (enVoice) utterance.voice = enVoice;
    }

    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-950 to-slate-900 border border-amber-500/30 shadow-xl space-y-3">
      {/* Top Bar: Title & Language Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
            <Volume2 className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
              <span>Rural Voice Assistant</span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-normal">
                Audio Access
              </span>
            </h4>
          </div>
        </div>

        {/* Language Tabs */}
        <div className="flex items-center bg-slate-900 rounded-lg p-0.5 border border-slate-800 text-[11px] font-semibold">
          <button
            onClick={() => { window.speechSynthesis?.cancel(); setSpeaking(false); setLanguage('en'); }}
            className={`px-2 py-0.5 rounded transition ${language === 'en' ? 'bg-amber-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            English
          </button>
          <button
            onClick={() => { window.speechSynthesis?.cancel(); setSpeaking(false); setLanguage('te'); }}
            className={`px-2 py-0.5 rounded transition ${language === 'te' ? 'bg-amber-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            తెలుగు
          </button>
          <button
            onClick={() => { window.speechSynthesis?.cancel(); setSpeaking(false); setLanguage('hi'); }}
            className={`px-2 py-0.5 rounded transition ${language === 'hi' ? 'bg-amber-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            हिन्दी
          </button>
        </div>
      </div>

      {/* Spoken Text Card */}
      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 space-y-1">
        <div className="font-bold text-amber-400 text-[11px]">{currentContent.title}</div>
        <p className="leading-relaxed text-[11px] text-slate-300">{currentContent.text}</p>
        <p className="text-[10px] text-slate-400 italic mt-1">💡 {currentContent.advice}</p>
      </div>

      {/* Voice Action Button */}
      <button
        onClick={handleSpeak}
        className={`w-full py-2 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg ${
          speaking
            ? 'bg-rose-500 text-white animate-pulse'
            : 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
        }`}
      >
        {speaking ? (
          <>
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>Stop Spoken Audio</span>
          </>
        ) : (
          <>
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Play Spoken Audio ({language.toUpperCase()})</span>
          </>
        )}
      </button>
    </div>
  );
}
