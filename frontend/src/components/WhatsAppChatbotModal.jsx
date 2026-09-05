import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Mic, Volume2, Globe, Check, CheckCheck, X, Bot, User, Sparkles } from 'lucide-react';

export default function WhatsAppChatbotModal({ isOpen, onClose, onSelectParcel }) {
  const [language, setLanguage] = useState('tel'); // 'tel' | 'hin' | 'ori' | 'eng'
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'నమస్కారం! నేను భునేత్ర AI ల్యాండ్ అసిస్టెంట్. మీ భూమి వివరాలు, మ్యుటేషన్ స్థితి లేదా సర్వే నంబర్ సమాచారం కోసం నన్ను అడగండి.\n(Namaskaram! I am BhuNetra AI WhatsApp Assistant. Ask me about RoR records, mutation status, or survey numbers).',
      time: '14:20'
    }
  ]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!isOpen) return null;

  const handleSend = (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim()) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');

    // Generate intelligent response based on language & intent
    setTimeout(() => {
      let reply = '';
      const tLower = text.toLowerCase();

      if (tLower.includes('45') || tLower.includes('102') || tLower.includes('sudrusti') || tLower.includes('odisha') || tLower.includes('భూమి')) {
        reply = language === 'tel'
          ? '✅ మీ భూమి రికార్డు కనుగొనబడింది!\n📍 సర్వే నం: 45/0, ఖాతా 102 (ఛత్రపూర్, గంజాం)\n👤 యజమాని: సుదృష్టి సేథీ\n📐 విస్తీర్ణం: 1,250 చ.మీ (వ్యవసాయ భూమి)\n🛡️ భునేత్ర టైటిల్ స్కోర్: 100% క్లీన్ (కోర్టు స్టే లేదు).'
          : (language === 'ori'
            ? '✅ ଆପଣଙ୍କ ଜମି ରେକର୍ଡ ମିଳିଲା!\n📍 ଖସରା ନଂ: 45/0, ଖାତା: 102 (ଛତ୍ରପୁର, ଗଞ୍ଜାମ)\n👤 ପଟ୍ଟାଦାର: ସୁଦୃଷ୍ଟି ସେଠୀ\n📐 ରକବା: 1,250 ବର୍ଗ ମିଟର\n🛡️ ଭୁନେତ୍ର ସ୍ଥିତି: 100% ନିର୍ଭୁଲ ଟାଇଟଲ୍।'
            : '✅ Record Verified!\n📍 Survey No: 45/0, Khata: 102 (Chhatrapur, Ganjam)\n👤 Pattadar: Sudrusti Sethi\n📐 Area: 1,250 Sq.m (Clear Title)\n🛡️ BhuNetra Health: 100% Green (No Court Stay).');
      } else if (tLower.includes('mutation') || tLower.includes('status') || tLower.includes('మ్యుటేషన్')) {
        reply = language === 'tel'
          ? '📋 మీ మ్యుటేషన్ అప్లికేషన్ MUT-2026-0412 ప్రస్తుతం "పబ్లిక్ నోటీసు పీరియడ్ (30 రోజులు)" లో ఉంది. ఇంకా 12 రోజులు మిగిలి ఉన్నాయి. తహశీల్దార్ ఆమోదం త్వరలో జరుగుతుంది.'
          : '📋 Mutation Application MUT-2026-0412 is currently in "Public Notice Period". 12 days remaining for final Tahsildar approval.';
      } else {
        reply = language === 'tel'
          ? 'ధన్యవాదాలు. మీ అభ్యర్థన భునేత్ర డేటాబేస్‌తో సమన్వయం చేయబడింది. మీరు ఏ సర్వే నంబర్ వివరాలు చూడాలనుకుంటున్నారు? (ఉదా: 45/0 లేదా 105)'
          : 'Thank you. How else can I assist with your land record verification today? You can provide a Survey / Khasra number to inspect.';
      }

      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="bg-[#0b141a] border border-slate-800 rounded-2xl w-full max-w-md h-[580px] overflow-hidden flex flex-col shadow-2xl">
        {/* WhatsApp Top Green Bar */}
        <div className="bg-[#1f2c34] p-3 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center text-white font-bold shadow">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h4 className="text-sm font-bold text-slate-100">BhuNetra Land AI</h4>
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
              </div>
              <p className="text-[10px] text-slate-400">Official WhatsApp Assistant · 24/7</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Selector */}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-[#111b21] border border-slate-700 text-emerald-400 text-[10px] font-bold rounded-lg px-2 py-1 focus:outline-none cursor-pointer"
            >
              <option value="tel">తెలుగు (Telugu)</option>
              <option value="hin">हिन्दी (Hindi)</option>
              <option value="ori">ଓଡ଼ିଆ (Odia)</option>
              <option value="eng">English</option>
            </select>
            <button onClick={onClose} className="text-slate-400 hover:text-white p-1">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Chat Messages Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#0b141a] bg-opacity-95">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col max-w-[85%] ${
                msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'
              }`}
            >
              <div
                className={`p-3 rounded-2xl text-xs whitespace-pre-wrap leading-relaxed shadow ${
                  msg.sender === 'user'
                    ? 'bg-[#005c4b] text-slate-100 rounded-tr-none'
                    : 'bg-[#202c33] text-slate-200 rounded-tl-none border border-slate-800'
                }`}
              >
                {msg.text}
              </div>
              <span className="text-[9px] text-slate-500 font-mono mt-0.5 px-1 flex items-center gap-1">
                {msg.time}
                {msg.sender === 'user' && <CheckCheck className="w-3 h-3 text-cyan-400" />}
              </span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-3 py-1.5 bg-[#111b21] border-t border-slate-800/80 flex items-center gap-1.5 overflow-x-auto text-[10px]">
          <button
            onClick={() => handleSend(language === 'tel' ? 'నా భూమి వివరాలు చూపించు (ఖస్రా 45/0)' : 'Show my land RoR details (Khata 102)')}
            className="px-2 py-1 rounded-full bg-[#202c33] hover:bg-[#2a3942] text-emerald-400 font-semibold border border-slate-700 whitespace-nowrap cursor-pointer"
          >
            🌾 {language === 'tel' ? 'నా భూమి రికార్డు' : 'My Land RoR'}
          </button>
          <button
            onClick={() => handleSend(language === 'tel' ? 'మ్యుటేషన్ స్థితి ఏమిటి?' : 'What is my mutation status?')}
            className="px-2 py-1 rounded-full bg-[#202c33] hover:bg-[#2a3942] text-amber-400 font-semibold border border-slate-700 whitespace-nowrap cursor-pointer"
          >
            📋 {language === 'tel' ? 'మ్యుటేషన్ స్థితి' : 'Mutation Status'}
          </button>
        </div>

        {/* Input Bar */}
        <div className="p-2.5 bg-[#202c33] flex items-center gap-2 border-t border-slate-800">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={language === 'tel' ? 'సందేశం టైప్ చేయండి...' : 'Type your land query in any Indian language...'}
            className="flex-1 bg-[#2a3942] rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none font-sans"
          />
          <button
            onClick={() => handleSend()}
            className="w-9 h-9 rounded-full bg-[#00a884] hover:bg-[#029070] text-slate-950 flex items-center justify-center transition cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
