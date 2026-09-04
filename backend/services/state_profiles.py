"""
backend/services/state_profiles.py — Dynamic State Profiles & Multilingual Cadastral Terminology for Pan-India Land Records.

Configures multilingual keyword dictionaries, administrative hierarchies, land unit systems,
and extraction profiles for all major Indian states and Union Territories.
"""

from __future__ import annotations
from typing import Any, Dict, List

STATE_PROFILES: Dict[str, Dict[str, Any]] = {
    "Odisha": {
        "name": "Odisha",
        "native_names": ["ଓଡ଼ିଶା", "ଓଡିଶା", "ओडिशा", "Orissa", "Odisha"],
        "portal_name": "Odisha Bhulekh",
        "script": "Odia",
        "state_keywords": [
            "ଓଡ଼ିଶା", "ଓଡିଶା", "ଓଡିଶା ସରକାର", "ଭୂଲେଖ", "ବେଗୁନିଆ", "ଖୋର୍ଦ୍ଧା", "ଟାଙ୍ଗି",
            "Schedule 1 Form No.39-A", "Schedule 1", "Form No.39-A", "Form 39-A",
            "Odisha", "Orissa", "Bhulekh", "Khordha", "Bhubaneswar", "Cuttack", "Puri"
        ],
        "districts": [
            "ଖୋର୍ଦ୍ଧା", "କଟକ", "ପୁରୀ", "ଗଞ୍ଜାମ", "ସମ୍ବଲପୁର", "ବାଲେଶ୍ୱର", "ଭଦ୍ରକ", "ସୁନ୍ଦରଗଡ଼",
            "ଅନୁଗୋଳ", "ବଲାଙ୍ଗୀର", "ବରଗଡ଼", "ଯାଜପୁର", "କେନ୍ଦ୍ରାପଡ଼ା", "ମୟୂରଭଞ୍ଜ", "ଜଗତସିଂହପୁର",
            "Khordha", "Khurda", "Cuttack", "Puri", "Ganjam", "Sambalpur", "Balasore", "Bhadrak"
        ],
        "subdistricts": [
            "ଟାଙ୍ଗି", "ବେଗୁନିଆ", "ଭୁବନେଶ୍ୱର", "ଜଟଣୀ", "ବାଲିଅନ୍ତା", "ବାଲିପାଟଣା", "ଚନ୍ଦକା",
            "Tangi", "Begunia", "Bhubaneswar", "Jatni", "Balianta", "Balipatna", "Chandaka"
        ],
        "district_keywords": ["ଜିଲ୍ଲା", "District", "ଜିଲ୍ଲା:"],
        "mandal_keywords": ["ତହସିଲ", "ତହସିଲ:", "ଥାନା", "ଥାନା:", "ତହସିଲଦାର", "Tahasil", "Tehsil", "Thana"],
        "village_keywords": ["ମୌଜା", "ମୌଜା:", "ଗାଁ", "ଗ୍ରାମ", "ବା: ନିଜଗାଁ", "Mauza", "Village", "Gram"],
        "khata_keywords": [
            "ଖତିୟାନର କ୍ରମିକ ନମ୍ବର", "ଖତିୟାନ", "ଖାତା", "ଥାନା ନମ୍ବର", "ଥାଜା ନମ୍ବର", "ଖେୱାଟ ନମ୍ବର",
            "Khata", "Khata No", "Khatian", "Khatian No", "Thana No"
        ],
        "plot_keywords": [
            "ତହସିଲ ନମ୍ବର", "ପ୍ଲଟ୍", "ପ୍ଲଟ", "ପ୍ଲଟ୍ ନମ୍ବର", "ଚକ", "Plot", "Plot No", "Plot Number"
        ],
        "survey_keywords": [
            "ତହସିଲ ନମ୍ବର", "ପ୍ଲଟ୍", "ପ୍ଲଟ", "ସର୍ଭେ", "Survey No", "Plot No"
        ],
        "owner_keywords": [
            "ପ୍ରଜାର ନାମ", "ରୟତ", "ଜମିଦାରଙ୍କ ନାମ", "ଖାତାଦାର", "ମାଲିକ", "ଭୂମିସ୍ୱାମୀ",
            "Praja Name", "Raiyat", "Rayat", "Owner", "Pattadar"
        ],
        "father_keywords": [
            "ପିତାର ନାମ", "ପି:", "ସ୍ୱାମୀ", "ବାପା", "Father", "Husband", "S/o", "W/o"
        ],
        "area_keywords": [
            "ରକବା", "କ୍ଷେତ୍ରଫଳ", "ଡେସିମିଲି", "ଏକର", "ହେକ୍ଟର", "Area", "Extent", "Decimal", "Acres", "Hectare"
        ],
        "land_use_keywords": [
            "କିସମ", "ସ୍ଥିତିବାନ", "ଘରବାରୀ", "ଜଳସେଚିତ", "ତୈଳବୀଜ", "ଶାରଦ", "Land Use", "Classification", "Sthitiban", "Gharabari"
        ],
        "deed_registration_keywords": [
            "Schedule 1 Form No.39-A", "Schedule 1", "Form 39-A", "ଖେୱାଟ ନମ୍ବର", "ଦଲିଲ ନମ୍ବର", "ପଞ୍ଜୀକରଣ", "Deed No", "Reg No"
        ],
        "ulpin_keywords": [
            "ଭୂ-ଆଧାର", "ULPIN", "Unique Land Parcel ID", "Unique ID"
        ]
    },

    "Telangana": {
        "name": "Telangana",
        "native_names": ["తెలంగాణ", "Telangana", "TS"],
        "portal_name": "Telangana Dharani",
        "script": "Telugu",
        "state_keywords": [
            "తెలంగాణ", "ధరణి", "Dharani", "Pattadar", "Telangana", "TS-DHARANI",
            "Shamshabad", "Rangareddy", "Mamidipally", "Kothwalguda", "CCLA"
        ],
        "districts": [
            "రంగా రెడ్డి", "రంగారెడ్డి", "హైదరాబాద్", "మేడ్చల్", "సంగారెడ్డి", "నల్గొండ", "వరంగల్",
            "Rangareddy", "Hyderabad", "Medchal", "Sangareddy", "Nalgonda", "Warangal"
        ],
        "subdistricts": [
            "శంషాబాద్", "రాజేంద్రనగర్", "కూకట్‌పల్లి", "శేరిలింగంపల్లి", "గండిపేట్",
            "Shamshabad", "Rajendranagar", "Kukatpally", "Serilingampally", "Gandipet"
        ],
        "district_keywords": ["జిల్లా", "District"],
        "mandal_keywords": ["మండలం", "తాలూకా", "Mandal", "Tehsil"],
        "village_keywords": ["గ్రామం", "గ్రామము", "Village", "Mauza"],
        "khata_keywords": ["ఖాతా నం", "ఖాతా నంబర్", "పాస్‌బుక్", "Khata", "Khatian", "Passbook No"],
        "plot_keywords": ["సర్వే నంబర్", "సర్వే నం", "సబ్-డివిజన్", "Survey No", "Sub-division"],
        "survey_keywords": ["సర్వే నంబర్", "సర్వే నం", "Survey No"],
        "owner_keywords": ["పట్టాదారు పేరు", "పట్టాదారు", "యజమాని", "Pattadar", "Owner Name"],
        "father_keywords": ["తండ్రి / భర్త పేరు", "తండ్రి పేరు", "భర్త పేరు", "Father Name", "Husband Name"],
        "area_keywords": ["విస్తీర్ణం", "ఎకరాలు", "గుంటలు", "చ.మీ", "Area", "Extent", "Acres", "Guntas"],
        "land_use_keywords": ["భూ వర్గీకరణ", "భూమి రకం", "Land Classification", "Land Use"],
        "deed_registration_keywords": ["దస్తావేజు నమోదు సంఖ్య", "నమోదు సంఖ్య", "Deed Registration No", "TS-DHARANI"],
        "ulpin_keywords": ["యుఎల్పిఐఎన్", "ULPIN", "Bhu-Aadhaar"]
    },

    "Uttar Pradesh": {
        "name": "Uttar Pradesh",
        "native_names": ["उत्तर प्रदेश", "Uttar Pradesh", "UP"],
        "portal_name": "UP Bhulekh",
        "script": "Devanagari",
        "state_keywords": [
            "उत्तर प्रदेश", "भूलेख", "खतौनी", "खसरा", "गाटा", "UP Bhulekh",
            "Lucknow", "Dehramau", "Mohanlalganj", "Kanpur", "Varanasi", "Prayagraj"
        ],
        "districts": [
            "लखनऊ", "कानपुर", "वाराणसी", "प्रयागराज", "आगरा", "गाजियाबाद", "नोएडा", "मेरठ", "गोरखपुर", "बरेली",
            "Lucknow", "Kanpur", "Varanasi", "Prayagraj", "Agra", "Ghaziabad", "Noida", "Meerut"
        ],
        "subdistricts": [
            "मोहनलालगंज", "सदर", "मलिहाबाद", "बक्शी का तालाब", "Mohanlalganj", "Sadar", "Malihabad"
        ],
        "district_keywords": ["जिला", "District", "जनपद"],
        "mandal_keywords": ["तहसील", "परगना", "ब्लॉक", "Tehsil", "Pargana"],
        "village_keywords": ["ग्राम", "गांव", "मौजा", "Village", "Mauza"],
        "khata_keywords": ["खाता संख्या", "खतौनी संख्या", "खाता", "खतौनी", "Khata", "Khatauni", "Khewat"],
        "plot_keywords": ["खसरा संख्या", "गाटा संख्या", "खसरा नं", "गाटा सं", "Khasra", "Gata No", "Plot"],
        "survey_keywords": ["खसरा संख्या", "गाटा संख्या", "Khasra No", "Survey No"],
        "owner_keywords": ["खातेदार का नाम", "काश्तकार", "भूमि स्वामी", "क्रेता", "पट्टेदार", "Khatedar", "Owner"],
        "father_keywords": ["पिता / पति का नाम", "पिता का नाम", "पति का नाम", "Father Name", "Husband Name"],
        "area_keywords": ["रकबा", "क्षेत्रफल", "हेक्टेयर", "वर्ग मीटर", "Area", "Extent", "Hectare", "Sqm"],
        "land_use_keywords": ["भूमि वर्गीकरण", "उपयोग", "Land Use", "Classification"],
        "deed_registration_keywords": ["दस्तावेज़ संख्या", "बैनामा संख्या", "विलेख पंजीकरण", "Deed No", "Reg No"],
        "ulpin_keywords": ["भू-आधार", "गाटा यूनिक कोड", "ULPIN"]
    },

    "Maharashtra": {
        "name": "Maharashtra",
        "native_names": ["महाराष्ट्र", "Maharashtra", "MH"],
        "portal_name": "Maharashtra Mahabhulekh",
        "script": "Devanagari",
        "state_keywords": [
            "महाराष्ट्र", "सातबारा", "7/12", "महाभूलेख", "Mahabhulekh", "Satbara", "Gat", "Pune", "Haveli", "Wagholi"
        ],
        "districts": [
            "पुणे", "मुंबई", "ठाणे", "नागपूर", "नाशिक", "औरंगाबाद", "सातारा", "कोल्हापूर", "सोलापूर",
            "Pune", "Mumbai", "Thane", "Nagpur", "Nashik", "Satara", "Kolhapur"
        ],
        "subdistricts": ["हवेली", "मुळशी", "मावळ", "शिरूर", "बारामती", "Haveli", "Mulshi", "Maval", "Shirur"],
        "district_keywords": ["जिल्हा", "District"],
        "mandal_keywords": ["तालुका", "Taluka", "Tehsil"],
        "village_keywords": ["गाव", "मौजे", "Village"],
        "khata_keywords": ["खाते क्रमांक", "खाते नं", "Khate No", "7/12"],
        "plot_keywords": ["गट क्रमांक", "गट नं", "सर्व्हे नंबर", "Gat No", "Survey No"],
        "survey_keywords": ["सर्व्हे नंबर", "गट क्रमांक", "Survey No", "Gat No"],
        "owner_keywords": ["खातेदाराचे नाव", "भोगवटादार", "जमीनदार", "Owner Name", "Bhogvatdar"],
        "father_keywords": ["वडिलांचे नाव", "पतीचे नाव", "Father Name"],
        "area_keywords": ["क्षेत्र", "हेक्टर", "आर", "गुंठा", "Area", "Hectare", "Guntha"],
        "land_use_keywords": ["धारणा प्रकार", "जिरायत", "बागायत", "Land Use"],
        "deed_registration_keywords": ["दस्त क्रमांक", "नोंदणी क्रमांक", "Deed No", "Registration No"],
        "ulpin_keywords": ["भू-आधार", "ULPIN"]
    },

    "Karnataka": {
        "name": "Karnataka",
        "native_names": ["ಕರ್ನಾಟಕ", "Karnataka", "KA"],
        "portal_name": "Karnataka Bhoomi",
        "script": "Kannada",
        "state_keywords": [
            "ಕರ್ನಾಟಕ", "ಭೂಮಿ", "ಪಹಣಿ", "RTC", "Pahani", "Bhoomi", "Karnataka", "Bengaluru", "Bangalore"
        ],
        "districts": ["ಬೆಂಗಳೂರು", "ಮೈಸೂರು", "ಬೆಳಗಾವಿ", "ಹುಬ್ಬಳ್ಳಿ", "ಮಂಗಳೂರು", "Bengaluru", "Mysuru", "Belagavi"],
        "subdistricts": ["ತಾಲೂಕು", "Taluk", "Hobli"],
        "district_keywords": ["ಜಿಲ್ಲೆ", "District"],
        "mandal_keywords": ["ತಾಲೂಕು", "Taluk"],
        "village_keywords": ["ಗ್ರಾಮ", "Village"],
        "khata_keywords": ["ಖಾತೆ ನಂ", "ಖಾತೆ ಸಂಖ್ಯೆ", "Khata No"],
        "plot_keywords": ["ಸರ್ವೆ ನಂಬರ್", "ಹಿಸ್ಸಾ ನಂ", "Survey No", "Hissa No"],
        "survey_keywords": ["ಸರ್ವೆ ನಂಬರ್", "Survey No"],
        "owner_keywords": ["ಮಾಲೀಕರ ಹೆಸರು", "ಖಾತೆದಾರರು", "Owner Name"],
        "father_keywords": ["ತಂದೆ ಹೆಸರು", "Father Name"],
        "area_keywords": ["ವಿಸ್ತೀರ್ಣ", "ಎಕರೆ", "ಗುಂಟೆ", "Area", "Acre", "Gunte"],
        "land_use_keywords": ["ಭೂಮಿ ವಿವರ", "ತರಿ", "ಖುಷ್ಕಿ", "ಬಾಗಾಯ್ತು", "Land Classification"],
        "deed_registration_keywords": ["ನೋಂದಣಿ ಸಂಖ್ಯೆ", "Deed No", "Registration No"],
        "ulpin_keywords": ["ಭೂ-ಆಧಾರ್", "ULPIN"]
    },

    "West Bengal": {
        "name": "West Bengal",
        "native_names": ["পশ্চিমবঙ্গ", "West Bengal", "WB"],
        "portal_name": "Banglarbhumi",
        "script": "Bengali",
        "state_keywords": [
            "পশ্চিমবঙ্গ", "বাংলারভূমি", "খতিয়ান", "দাগ", "Banglarbhumi", "West Bengal", "Kolkata", "Howrah"
        ],
        "districts": ["কলকাতা", "হাওড়া", "উত্তর ২৪ পরগনা", "দক্ষিণ ২৪ পরগনা", "হুগলী", "Kolkata", "Howrah", "Hooghly"],
        "subdistricts": ["ব্লক", "থানা", "Block", "Thana"],
        "district_keywords": ["জেলা", "District"],
        "mandal_keywords": ["ব্লক", "থানা", "Block", "Thana"],
        "village_keywords": ["মৌজা", "গ্রাম", "Mauza", "Village", "J.L. No"],
        "khata_keywords": ["খতিয়ান নং", "খতিয়ান", "Khatian No", "Khatian"],
        "plot_keywords": ["দাগ নং", "দাগ", "প্লট", "Dag No", "Plot No"],
        "survey_keywords": ["দাগ নং", "সার্ভে নং", "Dag No", "Survey No"],
        "owner_keywords": ["রায়তের নাম", "মালিকের নাম", "Rayat", "Owner Name"],
        "father_keywords": ["পিতার নাম", "স্বামীর নাম", "Father Name", "Husband Name"],
        "area_keywords": ["জমির পরিমাণ", "একড়", "শতক", "কাঠা", "Area", "Acre", "Satak"],
        "land_use_keywords": ["জমির শ্রেণী", "বাস্তু", "শালি", "Land Use"],
        "deed_registration_keywords": ["দলিল নম্বর", "রেজিস্ট্রেশন নম্বর", "Deed No"],
        "ulpin_keywords": ["ভু-আধার", "ULPIN"]
    },

    "Tamil Nadu": {
        "name": "Tamil Nadu",
        "native_names": ["தமிழ்நாடு", "Tamil Nadu", "TN"],
        "portal_name": "Tamil Nadu Patta Chitta",
        "script": "Tamil",
        "state_keywords": [
            "தமிழ்நாடு", "பட்டா", "சிட்டா", "Tamil Nadu", "Patta", "Chitta",
            "Chennai", "Kanchipuram", "Sriperumbudur", "Coimbatore"
        ],
        "districts": ["சென்னை", "காஞ்சிபுரம்", "செங்கல்பட்டு", "கோயம்புத்தூர்", "மதுரை", "Chennai", "Kanchipuram", "Coimbatore"],
        "subdistricts": ["வட்டம்", "Taluk"],
        "district_keywords": ["மாவட்டம்", "District"],
        "mandal_keywords": ["வட்டம்", "Taluk"],
        "village_keywords": ["கிராமம்", "Village"],
        "khata_keywords": ["பட்டா எண்", "கணக்கு எண்", "Patta No", "Chitta No"],
        "plot_keywords": ["புல எண்", "உட்பிரிவு எண்", "Survey No", "Sub-division"],
        "survey_keywords": ["புல எண்", "Survey No"],
        "owner_keywords": ["பட்டாதாரர் பெயர்", "உரிமையாளர் பெயர்", "Pattadar Name", "Owner"],
        "father_keywords": ["தந்தை பெயர்", "கணவர் பெயர்", "Father Name", "Husband Name"],
        "area_keywords": ["பரப்பு", "ஹெக்டேர்", "ஏக்கர்", "சென்ட்", "Area", "Cent", "Acre", "Hectare"],
        "land_use_keywords": ["நில வகைப்பாடு", "நஞ்சை", "புஞ்சை", "நத்தம்", "Land Classification"],
        "deed_registration_keywords": ["ஆவண எண்", "பதிவு எண்", "Deed No", "Registration No"],
        "ulpin_keywords": ["பூ-ஆதார்", "ULPIN"]
    },

    "Bihar": {
        "name": "Bihar",
        "native_names": ["बिहार", "Bihar"],
        "portal_name": "Bihar Bhumi",
        "script": "Devanagari",
        "state_keywords": ["बिहार", "बिहार भूमि", "जमाबंदी", "दाखिल खारिज", "Bihar", "Bihar Bhumi", "Patna", "Gaya"],
        "districts": ["पटना", "गया", "मुजफ्फरपुर", "भागलपुर", "दरभंगा", "Patna", "Gaya", "Muzaffarpur"],
        "subdistricts": ["अंचल", "प्रखंड", "Anchal", "Block"],
        "district_keywords": ["जिला", "District"],
        "mandal_keywords": ["अंचल", "प्रखंड", "थाना", "Anchal", "Circle"],
        "village_keywords": ["मौजा", "ग्राम", "थाना नं", "Mauza", "Village"],
        "khata_keywords": ["खाता संख्या", "जमाबंदी संख्या", "Khata No", "Jamabandi No"],
        "plot_keywords": ["खेसरा संख्या", "प्लाट संख्या", "Khesra No", "Plot No"],
        "survey_keywords": ["खेसरा संख्या", "Khesra No", "Survey No"],
        "owner_keywords": ["रैयत का नाम", "जमाबंदीदार", "Raiyat Name", "Owner"],
        "father_keywords": ["पिता का नाम", "Father Name"],
        "area_keywords": ["रकबा", "एकड़", "कट्ठा", "धूर", "Area", "Katha", "Dhur"],
        "land_use_keywords": ["जमीन का किस्म", "कृषि", "आवासीय", "Land Use"],
        "deed_registration_keywords": ["दस्तावेज संख्या", "Deed No", "Reg No"],
        "ulpin_keywords": ["भू-आधार", "ULPIN"]
    },

    "Rajasthan": {
        "name": "Rajasthan",
        "native_names": ["राजस्थान", "Rajasthan", "RJ"],
        "portal_name": "Rajasthan Apna Khata",
        "script": "Devanagari",
        "state_keywords": ["राजस्थान", "अपना खाता", "ई-धरती", "Rajasthan", "Apna Khata", "Bhilwara", "Mandalgarh", "Jaipur"],
        "districts": ["भीलवाड़ा", "जयपुर", "उदयपुर", "जोधपुर", "अजमेर", "कोटा", "Bhilwara", "Jaipur", "Udaipur"],
        "subdistricts": ["मांडलगढ़", "सांगानेर", "आमेर", "Mandalgarh", "Sanganer"],
        "district_keywords": ["जिला", "District"],
        "mandal_keywords": ["तहसील", "Tehsil"],
        "village_keywords": ["ग्राम", "गांव", "पटवार हलका", "Village", "Patwar"],
        "khata_keywords": ["खाता संख्या", "खतौनी संख्या", "खेवट", "Khata No", "Khewat"],
        "plot_keywords": ["खसरा संख्या", "Khasra No", "Plot No"],
        "survey_keywords": ["खसरा संख्या", "Khasra No", "Survey No"],
        "owner_keywords": ["खातेदार का नाम", "काश्तकार", "Khatedar", "Owner"],
        "father_keywords": ["पिता का नाम", "Father Name"],
        "area_keywords": ["रकबा", "क्षेत्रफल", "बीघा", "बिस्वा", "Area", "Bigha", "Biswa"],
        "land_use_keywords": ["भूमि वर्गीकरण", "बारानी", "चाही", "Land Classification"],
        "deed_registration_keywords": ["पंजीकरण संख्या", "विलेख संख्या", "Deed No"],
        "ulpin_keywords": ["भू-आधार", "ULPIN"]
    },

    "Delhi": {
        "name": "Delhi",
        "native_names": ["दिल्ली", "Delhi", "DL"],
        "portal_name": "Delhi DORIS",
        "script": "Latin/Devanagari",
        "state_keywords": ["दिल्ली", "Delhi", "DORIS", "Sangam Vihar", "South Delhi", "Shahdara", "GPA", "General Power of Attorney"],
        "districts": ["South Delhi", "New Delhi", "North Delhi", "East Delhi", "West Delhi", "दक्षिण दिल्ली"],
        "subdistricts": ["Saket", "Hauz Khas", "Mehrauli", "साकेत", "महरौली"],
        "district_keywords": ["District", "जिला"],
        "mandal_keywords": ["Sub-Division", "Tehsil", "तहसील"],
        "village_keywords": ["Village", "Locality", "Colony", "Sangam Vihar", "कॉलोनी"],
        "khata_keywords": ["Khata No", "Property No", "खाता संख्या"],
        "plot_keywords": ["Khasra No", "Plot No", "खसरा संख्या"],
        "survey_keywords": ["Khasra No", "Survey No"],
        "owner_keywords": ["Owner Name", "Executant", "GPA Holder", "मालिक का नाम"],
        "father_keywords": ["Father Name", "Husband Name", "पिता का नाम"],
        "area_keywords": ["Area", "Sq Yds", "Sq Metres", "वर्ग गज"],
        "land_use_keywords": ["Land Use", "Residential", "Commercial", "आवासीय"],
        "deed_registration_keywords": ["Registration No", "GPA No", "पंजीकरण संख्या"],
        "ulpin_keywords": ["ULPIN", "Bhu-Aadhaar"]
    }
}


def get_state_profile(state_name: str) -> Dict[str, Any]:
    """Retrieve profile for a state, falling back to a generic pan-India template if unlisted."""
    for s_name, prof in STATE_PROFILES.items():
        if s_name.lower() == state_name.lower():
            return prof
    return {
        "name": state_name or "Unknown",
        "native_names": [state_name] if state_name else [],
        "portal_name": f"{state_name} Land Records",
        "script": "Multilingual",
        "state_keywords": [state_name] if state_name else [],
        "districts": [],
        "subdistricts": [],
        "district_keywords": ["District", "जिला", "జిల్లా", "ଜିଲ୍ଲା", "மாவட்டம்", "জেলা"],
        "mandal_keywords": ["Tehsil", "Tahasil", "Mandal", "Taluk", "Block", "तहसील", "మండలం", "ତହସିଲ", "வட்டம்"],
        "village_keywords": ["Village", "Mauza", "Gram", "ग्राम", "मौजा", "గ్రామం", "ମୌଜା", "கிராமம்"],
        "khata_keywords": ["Khata", "Khatian", "Patta", "खाता", "खतौनी", "ఖాతా", "ଖତିୟାନ", "பட்டா"],
        "plot_keywords": ["Plot", "Survey", "Khasra", "Gata", "Dagar", "खसरा", "सर्वे", "ପ୍ଲଟ୍", "புல எண்"],
        "survey_keywords": ["Survey No", "Khasra No", "Plot No", "सर्वे नं", "ପ୍ଲଟ୍"],
        "owner_keywords": ["Owner", "Pattadar", "Khatedar", "Raiyat", "खातेदार", "పట్టాదారు", "ପ୍ରଜାର ନାମ", "பட்டாதாரர்"],
        "father_keywords": ["Father", "Husband", "पिता", "पति", "తండ్రి", "ପିତାର ନାମ", "தந்தை"],
        "area_keywords": ["Area", "Extent", "रकबा", "क्षेत्रफल", "విస్తీర్ణం", "କ୍ଷେତ୍ରଫଳ", "பரப்பு"],
        "land_use_keywords": ["Land Use", "Classification", "वर्गीकरण", "ସ୍ଥିତିବାନ", "வகைப்பாடு"],
        "deed_registration_keywords": ["Deed No", "Registration No", "पंजीकरण", "ଦସ୍ତାବେଜ", "பதிவு எண்"],
        "ulpin_keywords": ["ULPIN", "Bhu-Aadhaar", "भू-आधार"]
    }
