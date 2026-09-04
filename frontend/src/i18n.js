/**
 * i18n.js — Sovereign Indian Multilingual Integration with AI4Bharat IndicTransToolkit.
 *
 * Supports English (en), Hindi (hi), Telugu (te), Odia (or), Marathi (mr),
 * Bengali (bn), Tamil (ta), and Kannada (kn).
 *
 * Powered by IndicTransToolkit (https://github.com/VarunGumma/IndicTransToolkit.git).
 */
import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const LANG_KEY = 'bhunetra_lang';

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు', flag: '🏛️' },
  { code: 'or', name: 'Odia', native: 'ଓଡ଼ିଆ', flag: '📜' },
  { code: 'mr', name: 'Marathi', native: 'मराठी', flag: '🚩' },
  { code: 'bn', name: 'Bengali', native: 'বাংলা', flag: '🌾' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்', flag: '🛕' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ', flag: '🐘' },
];

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
    'tab.timeline': 'Risk Timeline',
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
    'btn.odisha_ror': 'Odisha RoR (ଭୂଲେଖ)',
    // Risk levels
    'risk.green': 'Low Risk',
    'risk.yellow': 'Moderate Risk',
    'risk.red': 'High Risk',
    // Common
    'common.parcel': 'Parcel',
    'common.village': 'Village',
    'common.mandal': 'Mandal / Tehsil',
    'common.status': 'Status',
    'common.risk_score': 'Risk Score',
    'common.verified': 'Verified',
    'common.clean': 'Clean',
    'common.unknown': 'Unknown',
  },
  hi: {
    'tab.map': 'भू-मानचित्र (GIS)',
    'tab.ocr': 'दस्तावेज़ डिजिटलीकरण (OCR)',
    'tab.ownership': 'स्वामित्व एवं वंशावली',
    'tab.satellite': 'उपग्रह सत्यापन (Satellite)',
    'tab.review': 'राजस्व अधिकारी समीक्षा',
    'tab.revenue': 'राजस्व न्यायालय (RCCMS)',
    'tab.analytics': 'प्रशासनिक विश्लेषण',
    'tab.documents': 'अभिलेख पंजिका',
    'tab.mutations': 'दाखिल-खारिज (नामांतरण)',
    'tab.batch': 'सामूहिक प्रसंस्करण',
    'tab.timeline': 'जोखिम समय-सीमा',
    'btn.approve': 'स्वीकृत करें',
    'btn.reject': 'अस्वीकृत करें',
    'btn.refresh': 'ताज़ा करें',
    'btn.search': 'गाटा / खसरा / भूखंड खोजें',
    'btn.print': 'मुद्रण',
    'btn.download_pdf': 'डिजिटल प्रमाण पत्र डाउनलोड',
    'btn.sign_record': 'डिजिटल हस्ताक्षर एवं हैश दर्ज करें',
    'btn.simulate_alert': 'नागरिक चेतावनी भेजें',
    'btn.watch_demo': 'प्रणाली डेमो देखें',
    'btn.skip': 'छोड़ें',
    'btn.odisha_ror': 'ओडिशा भूलेख (RoR)',
    'risk.green': 'सुरक्षित / कम जोखिम',
    'risk.yellow': 'मध्यम जोखिम (समीक्षाधीन)',
    'risk.red': 'उच्च जोखिम / विवादित',
    'common.parcel': 'भूखंड',
    'common.village': 'ग्राम / मौजा',
    'common.mandal': 'तहसील / ब्लॉक',
    'common.status': 'स्थिति',
    'common.risk_score': 'जोखिम सूचकांक',
    'common.verified': 'सत्यापित',
    'common.clean': 'विवाद-रहित',
    'common.unknown': 'अज्ञात',
  },
  te: {
    'tab.map': 'భూమి వివరాలు (GIS)',
    'tab.ocr': 'రిజిస్ట్రీ OCR',
    'tab.ownership': 'అమ్మకపు చరిత్ర & వంశావళి',
    'tab.satellite': 'శాటిలైట్ ధృవీకరణ',
    'tab.review': 'అధికారి సమీక్ష క్యూ',
    'tab.revenue': 'రెవెన్యూ కోర్ట్',
    'tab.analytics': 'కలెక్టర్ విశ్లేషణలు',
    'tab.documents': 'రిజిస్టర్డ్ పత్రాలు',
    'tab.mutations': 'మ్యుటేషన్లు & విభజన',
    'tab.batch': 'బ్యాచ్ ప్రాసెసింగ్',
    'tab.timeline': 'ప్రమాద కాలక్రమం',
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
    'btn.odisha_ror': 'ఒడిశా భూలేఖ్ (RoR)',
    'risk.green': 'తక్కువ ప్రమాదం',
    'risk.yellow': 'మధ్యస్థ ప్రమాదం',
    'risk.red': 'అధిక ప్రమాదం',
    'common.parcel': 'పార్సెల్',
    'common.village': 'గ్రామం',
    'common.mandal': 'మండలం',
    'common.status': 'స్థితి',
    'common.risk_score': 'ప్రమాద స్కోర్',
    'common.verified': 'ధృవీకరించబడింది',
    'common.clean': 'శుభ్రం',
    'common.unknown': 'తెలియదు',
  },
  or: {
    'tab.map': 'ଭୂ-ନକ୍ସା (GIS Map)',
    'tab.ocr': 'ଦଲିଲ୍ ଡିଜିଟାଇଜେସନ (OCR)',
    'tab.ownership': 'ସ୍ୱତ୍ତ୍ୱ ଓ ମାଲିକାନା ଇତିହାସ',
    'tab.satellite': 'ସାଟେଲାଇଟ୍ ଯାଞ୍ଚ',
    'tab.review': 'ତହସିଲଦାର ସମୀକ୍ଷା',
    'tab.revenue': 'ରାଜସ୍ୱ ନ୍ୟାୟାଳୟ',
    'tab.analytics': 'ପ୍ରଶାସନିକ ବିଶ୍ଳେଷଣ',
    'tab.documents': 'ସ୍ୱତ୍ତ୍ୱ ଲିପି ପତ୍ର',
    'tab.mutations': 'ଦାଖଲ ଖାରଜ (Mutation)',
    'tab.batch': 'ଏକତ୍ର ପ୍ରକ୍ରିୟାକରଣ',
    'tab.timeline': 'ବିପଦ ସମୟରେଖା',
    'btn.approve': 'ମଞ୍ଜୁର କରନ୍ତୁ',
    'btn.reject': 'ଖାରଜ କରନ୍ତୁ',
    'btn.refresh': 'ତାଜା କରନ୍ତୁ',
    'btn.search': 'ଖାତା / ପ୍ଲଟ୍ / ରୟତ ଖୋଜନ୍ତୁ',
    'btn.print': 'ଛାପନ୍ତୁ',
    'btn.download_pdf': 'ସ୍ୱତ୍ତ୍ୱ ପ୍ରମାଣପତ୍ର ଡାଉନଲୋଡ୍',
    'btn.sign_record': 'ଡିଜିଟାଲ୍ ଦସ୍ତଖତ ଓ ହ୍ୟାଶ୍',
    'btn.simulate_alert': 'ଚେତାବନୀ ପଠାନ୍ତୁ',
    'btn.watch_demo': 'ଡେମୋ ଦେଖନ୍ତୁ',
    'btn.skip': 'ଏଡ଼ାଇ ଯାଆନ୍ତୁ',
    'btn.odisha_ror': 'ଓଡ଼ିଶା ଭୂଲେଖ (RoR)',
    'risk.green': 'ସୁରକ୍ଷିତ / କମ୍ ବିପଦ',
    'risk.yellow': 'ମଧ୍ୟମ ବିପଦ',
    'risk.red': 'ଉଚ୍ଚ ବିପଦ / ବିବାଦୀୟ',
    'common.parcel': 'ଜମି ପ୍ଲଟ୍',
    'common.village': 'ମୌଜା / ଗ୍ରାମ',
    'common.mandal': 'ତହସିଲ',
    'common.status': 'ସ୍ଥିତି',
    'common.risk_score': 'ବିପଦ ସୂଚକ',
    'common.verified': 'ଯାଞ୍ଚ ହୋଇଛି',
    'common.clean': 'ନିର୍ଦ୍ଦୋଷ ସ୍ୱତ୍ତ୍ୱ',
    'common.unknown': 'ଅଜ୍ଞାତ',
  },
  mr: {
    'tab.map': 'जमीन नकाशा (GIS)',
    'tab.ocr': 'दस्तऐवज स्कॅनिंग (OCR)',
    'tab.ownership': '७/१२ फेरफार व मालकी',
    'tab.satellite': 'उपग्रह पडताळणी',
    'tab.review': 'अधिकारी तपासणी',
    'tab.revenue': 'महसूल न्यायालय',
    'tab.analytics': 'जिल्हाधिकारी विश्लेषण',
    'tab.documents': 'दस्तऐवज नोंद',
    'tab.mutations': 'फेरफार नोंदी',
    'tab.batch': 'एकत्रित प्रक्रिया',
    'tab.timeline': 'जोखीम कालक्रम',
    'btn.approve': 'मंजूर करा',
    'btn.reject': 'फेटाळा',
    'btn.refresh': 'ताजे करा',
    'btn.search': 'गट क्र. / सर्व्हे क्र. शोधा',
    'btn.print': 'मुद्रित करा',
    'btn.download_pdf': 'प्रमाणपत्र डाउनलोड',
    'btn.sign_record': 'डिजिटल स्वाक्षरी नोंदवा',
    'btn.simulate_alert': 'सूचना पाठवा',
    'btn.watch_demo': 'डेमो पहा',
    'btn.skip': 'पुढे जा',
    'btn.odisha_ror': 'ओडिशा भूलेख (RoR)',
    'risk.green': 'कमी जोखीम (सुरक्षित)',
    'risk.yellow': 'मध्यम जोखीम',
    'risk.red': 'उच्च जोखीम (विवादित)',
    'common.parcel': 'जमीन गट',
    'common.village': 'गाव',
    'common.mandal': 'तालुका',
    'common.status': 'स्थिती',
    'common.risk_score': 'जोखीम गुण',
    'common.verified': 'पडताळणी पूर्ण',
    'common.clean': 'स्वच्छ',
    'common.unknown': 'अज्ञात',
  },
  bn: {
    'tab.map': 'জমি মানচিত্র (GIS)',
    'tab.ocr': 'দলিল ও পরচা OCR',
    'tab.ownership': 'খতিয়ান ও মালিকানা',
    'tab.satellite': 'স্যাটেলাইট যাচাই',
    'tab.review': 'রাজস্ব আধিকারিক পর্যালোচনা',
    'tab.revenue': 'রাজস্ব আদালত',
    'tab.analytics': 'জেলা বিশ্লেষণ',
    'tab.documents': 'নথিপত্র',
    'tab.mutations': 'নামজারি ও মিউটেশন',
    'tab.batch': 'ব্যাচ প্রসেস',
    'tab.timeline': 'ঝুঁকির সময়সীমা',
    'btn.approve': 'অনুমোদন করুন',
    'btn.reject': 'প্রত্যাখ্যান করুন',
    'btn.refresh': 'রিফ্রেশ',
    'btn.search': 'দাগ / খতিয়ান / প্লট খুঁজুন',
    'btn.print': 'প্রিন্ট',
    'btn.download_pdf': 'সার্টিফিকেট ডাউনলোড',
    'btn.sign_record': 'ডিজিটাল সই ও হ্যাশ',
    'btn.simulate_alert': 'সতর্কবার্তা পাঠান',
    'btn.watch_demo': 'ডেমো দেখুন',
    'btn.skip': 'এড়িয়ে যান',
    'btn.odisha_ror': 'ওড়িশা ভূলেখ (RoR)',
    'risk.green': 'কম ঝুঁকি (সুরক্ষিত)',
    'risk.yellow': 'মাঝারি ঝুঁকি',
    'risk.red': 'উচ্চ ঝুঁকি (বিতর্কিত)',
    'common.parcel': 'প্লট',
    'common.village': 'মৌজা / গ্রাম',
    'common.mandal': 'ব্লক / তহশিল',
    'common.status': 'স্থিতি',
    'common.risk_score': 'ঝুঁকি স্কোর',
    'common.verified': 'যাচাইকৃত',
    'common.clean': 'স্বচ্ছ',
    'common.unknown': 'অজানা',
  },
  ta: {
    'tab.map': 'நில வரைபடம் (GIS)',
    'tab.ocr': 'பத்திர ஸ்கேனிங் (OCR)',
    'tab.ownership': 'பட்டா & உரிமை வரலாறு',
    'tab.satellite': 'செயற்கைக்கோள் சரிபார்ப்பு',
    'tab.review': 'வருவாய் அதிகாரி சரிபார்ப்பு',
    'tab.revenue': 'வருவாய் நீதிமன்றம்',
    'tab.analytics': 'நிர்வாக பகுப்பாய்வு',
    'tab.documents': 'ஆவணங்கள்',
    'tab.mutations': 'பட்டா மாறுதல் (Mutation)',
    'tab.batch': 'தொகுதி செயலாக்கம்',
    'tab.timeline': 'அபாய காலவரிசை',
    'btn.approve': 'ஒப்புதல் அளி',
    'btn.reject': 'நிராகரி',
    'btn.refresh': 'புதுப்பி',
    'btn.search': 'சர்வே எண் / பட்டா தேடு',
    'btn.print': 'அச்சிடு',
    'btn.download_pdf': 'சான்றிதழ் பதிவிறக்கு',
    'btn.sign_record': 'டிஜிட்டல் கையொப்பம்',
    'btn.simulate_alert': 'எச்சரிக்கை அனுப்பு',
    'btn.watch_demo': 'டெமோ காண்க',
    'btn.skip': 'தவிர்',
    'btn.odisha_ror': 'ஒடிசா நில உரிமை (RoR)',
    'risk.green': 'குறைந்த அபாயம்',
    'risk.yellow': 'மிதமான அபாயம்',
    'risk.red': 'அதிக அபாயம்',
    'common.parcel': 'நிலப்பகுதி',
    'common.village': 'கிராமம்',
    'common.mandal': 'வட்டம் / தாலுகா',
    'common.status': 'நிலை',
    'common.risk_score': 'அபாய மதிப்பீடு',
    'common.verified': 'சரிபார்க்கப்பட்டது',
    'common.clean': 'தெளிவானது',
    'common.unknown': 'தெரியவில்லை',
  },
  kn: {
    'tab.map': 'ಭೂ ನಕ್ಷೆ (GIS)',
    'tab.ocr': 'ದಾಖಲೆ ಡಿಜಿಟಲೀಕರಣ (OCR)',
    'tab.ownership': 'ಪಹಣಿ & ಮಾಲೀಕತ್ವ',
    'tab.satellite': 'ಉಪಗ್ರಹ ಪರಿಶೀಲನೆ',
    'tab.review': 'ಕಂದಾಯ ಅಧಿಕಾರಿ ಪರಿಶೀಲನೆ',
    'tab.revenue': 'ಕಂದಾಯ ನ್ಯಾಯಾಲಯ',
    'tab.analytics': 'ಆಡಳಿತಾತ್ಮಕ ವಿಶ್ಲೇಷಣೆ',
    'tab.documents': 'ದಾಖಲೆಗಳು',
    'tab.mutations': 'ಮ್ಯುಟೇಶನ್ & ಖಾತೆ ಬದಲಾವಣೆ',
    'tab.batch': 'ಬ್ಯಾಚ್ ಪ್ರಕ್ರಿಯೆ',
    'tab.timeline': 'ಅಪಾಯದ ಕಾಲಾವಧಿ',
    'btn.approve': 'ಅನುಮೋದಿಸಿ',
    'btn.reject': 'ತಿರಸ್ಕರಿಸಿ',
    'btn.refresh': 'ನವೀಕರಿಸಿ',
    'btn.search': 'ಸರ್ವೆ ನಂ / ಖಾತೆ ಹುಡುಕಿ',
    'btn.print': 'ಮುದ್ರಿಸಿ',
    'btn.download_pdf': 'ಪ್ರಮಾಣಪತ್ರ ಡೌನ್‌ಲೋಡ್',
    'btn.sign_record': 'ಡಿಜಿಟಲ್ ಸಹಿ',
    'btn.simulate_alert': 'ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಿ',
    'btn.watch_demo': 'ಡೆಮೊ ವೀಕ್ಷಿಸಿ',
    'btn.skip': 'ಬಿಟ್ಟುಬಿಡಿ',
    'btn.odisha_ror': 'ಒಡಿಶಾ ಭೂಲೇಖ್ (RoR)',
    'risk.green': 'ಕಡಿಮೆ ಅಪಾಯ',
    'risk.yellow': 'ಮಧ್ಯಮ ಅಪಾಯ',
    'risk.red': 'ಹೆಚ್ಚಿನ ಅಪಾಯ',
    'common.parcel': 'ಭೂಖಂಡ',
    'common.village': 'ಗ್ರಾಮ',
    'common.mandal': 'ತಾಲೂಕು',
    'common.status': 'ಸ್ಥಿತಿ',
    'common.risk_score': 'ಅಪಾಯದ ಅಂಕ',
    'common.verified': 'ಪರಿಶೀಲಿಸಲಾಗಿದೆ',
    'common.clean': 'ಸ್ಪಷ್ಟ',
    'common.unknown': 'ತಿಳಿದಿಲ್ಲ',
  }
};

const dynamicCache = new Map();

const LangContext = createContext({
  lang: 'en',
  setLang: () => {},
  t: (k) => k,
  translateDynamic: async (text) => text,
  supportedLanguages: SUPPORTED_LANGUAGES
});

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

  // Real-time dynamic translation powered by Sarvam AI for backend dynamic strings
  const translateDynamic = useCallback(async (text, targetLanguage = lang) => {
    if (!text || typeof text !== 'string' || targetLanguage === 'en') return text;
    const cacheKey = `${targetLanguage}:${text.trim()}`;
    if (dynamicCache.has(cacheKey)) {
      return dynamicCache.get(cacheKey);
    }
    try {
      const res = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          target_language: targetLanguage,
          source_language: 'en'
        })
      });
      if (res.ok) {
        const json = await res.json();
        const result = json.translated_text || text;
        dynamicCache.set(cacheKey, result);
        return result;
      }
    } catch (e) {
      console.warn('Sarvam dynamic translation fallback', e);
    }
    return text;
  }, [lang]);

  const value = useMemo(() => ({
    lang,
    setLang,
    t,
    translateDynamic,
    supportedLanguages: SUPPORTED_LANGUAGES
  }), [lang, setLang, t, translateDynamic]);

  return React.createElement(LangContext.Provider, { value }, children);
}

export function useLang() {
  return useContext(LangContext);
}
