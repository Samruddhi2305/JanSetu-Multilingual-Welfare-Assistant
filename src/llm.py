import os
import json
import requests
import re
from src.search import screen_eligibility
from duckduckgo_search import DDGS

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

def get_gemini_response(prompt, context_schemes=None):
    """
    Calls the Gemini API directly via HTTP POST to generate a response.
    """
    if not GEMINI_API_KEY:
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    system_instruction = (
        "You are an Ultra-Low-Latency Welfare Scheme Awareness Chatbot. "
        "Answer questions in the user's language/dialect (Hindi, Tamil, or code-mixed like Hinglish/Tanglish). "
        "You must remain strictly grounded in the official scheme data provided in the context. "
        "If you do not know the answer or if it's not in the context, say: 'I do not have this information, please visit your nearest Gram Panchayat.' "
        "Do not hallucinate any eligibility criteria or document lists."
    )
    
    # Structure context
    context_str = ""
    if context_schemes:
        context_str = "CONTEXT SCHEMES:\n"
        for s in context_schemes:
            context_str += f"- ID: {s['id']}\n  Name: {s['name']}\n  Description: {s['description']}\n  Benefit: {s['benefit']}\n  Eligibility: {s['eligibility']['rules']}\n  Required Documents: {', '.join(s['documents'])}\n\n"
            
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\n{context_str}\n\nUser Message: {prompt}"}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            # Extract text content safely
            text = res_json['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
        else:
            print(f"Gemini API returned status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return None

def perform_web_search(query):
    """
    Performs a robust mock web search.
    Tries a local knowledge base first, then falls back to Wikipedia API.
    """
    q = query.lower()
    context = ""
    
    # Robust Offline Knowledge Base for Documents
    if any(w in q for w in ["income", "aay", "आय"]):
        context += "WEB SEARCH RESULTS (Gov Portal):\n- To get an Income Certificate: Visit your local Tahsildar office, Gram Panchayat, or the state's e-District portal. Required documents: Ration Card, Aadhaar Card, Passport size photo, and an affidavit.\n"
    elif any(w in q for w in ["land", "ownership", "khatata", "patta", "bhumi", "zamin", "jamin", "भूमि", "ज़मीन", "நிலம்", "சொத்து"]):
        context += "WEB SEARCH RESULTS (Revenue Dept):\n- To get Land Ownership Documents (Patta/Chitta/Khatouni): Visit the Revenue Department office (Patwari/Tahsildar) or the official land records portal of your state (e.g., Bhulekh, AnyRoR). Required documents: Previous deed, Aadhaar, and survey number.\n"
    elif any(w in q for w in ["ration", "राशन", "ரேஷன்"]):
        context += "WEB SEARCH RESULTS (PDS Portal):\n- To get a Ration Card: Apply at the Food and Civil Supplies office or online via the state portal. Required documents: Aadhaar, Income certificate, Address proof.\n"
        
    if context:
        return context

    # Fallback to Wikipedia API to pull information from the web
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "utf8": "",
            "format": "json"
        }
        headers = {'User-Agent': 'WelfareChatbot/1.0 (test@example.com)'}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get('query', {}).get('search', [])
            if results:
                context = "WEB SEARCH RESULTS (Wikipedia):\n"
                for r in results[:2]:
                    # Remove HTML tags from snippet
                    clean_snippet = re.sub(r'<[^>]+>', '', r.get('snippet', ''))
                    context += f"- {r.get('title', '')}: {clean_snippet}...\n"
                return context
    except Exception as e:
        print(f"Web search error: {e}")
        
    return ""

def local_indic_fallback_nlu(user_message, session_state, eligible_schemes):
    """
    A highly robust local rule-based NLU engine that acts as a local fallback model.
    It understands English, Hindi, Tamil, and code-mixed Hinglish/Tanglish.
    """
    msg = user_message.lower().strip()
    lang = session_state.get('lang', 'en')
    
    # Simple language detection from greeting or message characters
    if any(greet in msg for greet in ['namaste', 'pranam', 'hello', 'hi', 'kya', 'mera', 'kaise']):
        lang = 'hi'
    elif any(greet in msg for greet in ['vanakkam', 'enna', 'enathu', 'tamil', 'nalama']):
        lang = 'ta'
    session_state['lang'] = lang

    # Define language translations for bot messages
    templates = {
        'en': {
            'greet': "Hello! I am your NSS Welfare Scheme Assistant. I can help you find schemes you qualify for and lists of documents needed. Which language do you prefer? (1. English / 2. Hindi / 3. Tamil)",
            'ask_age': "To check your eligibility, please tell me: What is your age?",
            'ask_income': "What is your monthly or annual household income in Rupees?",
            'ask_occupation': "What is your main occupation or job? (e.g., Farmer, Gig Worker, Laborer, Student, Homemaker)",
            'ask_gender': "What is your gender? (Male/Female)",
            'no_schemes': "Based on the details, you do not seem to qualify for our current high-impact catalog. For more details, consult your Gram Panchayat.",
            'eligible_list': "Based on your details, here is a personalized list of schemes you qualify for:",
            'checklists': "Here is the checklist of required documents in English:",
            'footer': "\nGive a missed call anytime to trigger this guide over SMS for free!"
        },
        'hi': {
            'greet': "नमस्ते! मैं आपका एनएसएस कल्याणकारी योजना सहायक हूं। मैं आपकी पात्रता जांचने और आवश्यक दस्तावेजों की सूची बताने में मदद कर सकता हूं। अपनी पसंदीदा भाषा चुनें: (1. English / 2. हिंदी / 3. तमिल)",
            'ask_age': "आपकी पात्रता जांचने के लिए, कृपया बताएं: आपकी उम्र (Age) क्या है?",
            'ask_income': "आपकी मासिक या वार्षिक पारिवारिक आय (Monthly/Annual Income) कितनी है?",
            'ask_occupation': "आपका मुख्य व्यवसाय (Occupation) क्या है? (जैसे: किसान/Farmer, गिग वर्कर/Driver, मजदूर/Laborer, गृहणी/Homemaker)",
            'ask_gender': "आपका लिंग (Gender) क्या है? (पुरुष/Male या महिला/Female)",
            'no_schemes': "आपकी जानकारी के अनुसार, आप वर्तमान योजनाओं के लिए पात्र नहीं दिख रहे हैं। अधिक जानकारी के लिए ग्राम पंचायत से संपर्क करें।",
            'eligible_list': "आपकी जानकारी के अनुसार, आप इन योजनाओं के लिए पात्र हैं:",
            'checklists': "यहाँ आपकी योजनाओं के लिए आवश्यक दस्तावेजों की सूची (Hinglish) दी गई है:",
            'footer': "\nमुफ़्त में एसएमएस पर यह जानकारी पाने के लिए किसी भी समय इस नंबर पर मिस्ड कॉल दें!"
        },
        'ta': {
            'greet': "வணக்கம்! நான் உங்கள் NSS நலத்திட்ட உதவியாளர். உங்களுக்கு தகுதியான அரசு திட்டங்களை கண்டறிய நான் உதவுகிறேன். உங்களுக்கு பிடித்த மொழியை தேர்வு செய்யவும்: (1. English / 2. இந்தி / 3. தமிழ்)",
            'ask_age': "உங்கள் தகுதியை சரிபார்க்க, தயவுசெய்து கூறவும்: உங்கள் வயது (Age) என்ன?",
            'ask_income': "உங்கள் குடும்பத்தின் மாத அல்லது வருட வருமானம் (Income) எவ்வளவு?",
            'ask_occupation': "உங்கள் முக்கிய தொழில் (Occupation) என்ன? (எ.கா. விவசாயி/Farmer, ஓட்டுநர்/Driver, தொழிலாளி/Laborer, இல்லத்தரசி/Homemaker)",
            'ask_gender': "உங்கள் பாலினம் (Gender) என்ன? (ஆண்/Male அல்லது பெண்/Female)",
            'no_schemes': "வழங்கப்பட்ட விவரங்களின்படி, தற்போது தகுதியான திட்டங்கள் எதுவும் கண்டறியப்படவில்லை. மேலும் விவரங்களுக்கு கிராம பஞ்சாயத்தை அணுகவும்.",
            'eligible_list': "உங்கள் விவரங்களின்படி, உங்களுக்கு தகுதியான அரசு திட்டங்கள்:",
            'checklists': "தேவையான ஆவணங்களின் பட்டியல் (Tanglish):",
            'footer': "\nஇலவசமாக SMS மூலம் இந்த விவரங்களைப் பெற எந்த நேரத்திலும் மிஸ் கால் கொடுக்கவும்!"
        }
    }

    t = templates[lang]
    step = session_state.get('step', 'start')

    # 1. Start Step — show greeting and ask for language
    if step == 'start':
        session_state['step'] = 'lang'
        return t['greet']

    # 2. Language Selection Step
    if step == 'lang':
        if '1' in msg or 'english' in msg:
            session_state['lang'] = 'en'
            lang = 'en'
            t = templates['en']
        elif '2' in msg or 'hindi' in msg or 'हिंदी' in msg:
            session_state['lang'] = 'hi'
            lang = 'hi'
            t = templates['hi']
        elif '3' in msg or 'tamil' in msg or 'தமிழ்' in msg:
            session_state['lang'] = 'ta'
            lang = 'ta'
            t = templates['ta']
        session_state['step'] = 'age'
        return t['ask_age']

    # 3. Extract values dynamically from user message depending on the current step
    if step == 'age':
        nums = re.findall(r'\d+', msg)
        if nums:
            session_state['age'] = int(nums[0])
            session_state['step'] = 'income'
            return t['ask_income']
        else:
            return "Please enter your age in numbers (e.g. 35) / कृपया अपनी उम्र अंकों में दर्ज करें:"
            
    elif step == 'income':
        # Check for numbers and abbreviations like 'k', 'lakh'
        nums = re.findall(r'\d+', msg)
        if nums:
            val = int(nums[0])
            if 'k' in msg or 'thousand' in msg or 'हजार' in msg:
                val *= 1000
            elif 'lakh' in msg or 'लाख' in msg:
                val *= 100000
                
            # If it's small, assume monthly and convert to annual
            if val < 25000:
                val *= 12
                
            session_state['income'] = val
            session_state['step'] = 'occupation'
            return t['ask_occupation']
        else:
            return "Please enter your income in numbers (e.g. 10000) / कृपया अपनी आय अंकों में दर्ज करें:"
            
    elif step == 'occupation':
        # Map colloquial / Indic names to our target occupations
        occ = 'Unorganized Worker'
        if any(w in msg for w in ['kisan', 'kheti', 'farmer', 'farm', 'खेती', 'किसान', 'agriculture', 'vivasayam', 'vivasayi']):
            occ = 'Farmer'
        elif any(w in msg for w in ['labor', 'laborer', 'mazdoor', 'coolie', 'मजदूर', 'construction', 'velaikaarar', 'work']):
            occ = 'Laborer'
        elif any(w in msg for w in ['driver', 'gig', 'street', 'vendor', 'ola', 'uber', 'zomato', 'swiggy', 'shop']):
            occ = 'Gig Worker'
        elif any(w in msg for w in ['student', 'padhai', 'college', 'school', 'மாணவர்']):
            occ = 'Student'
        elif any(w in msg for w in ['housewife', 'homemaker', 'home', 'house', 'பெண்']):
            occ = 'Homemaker'
            
        session_state['occupation'] = occ
        session_state['step'] = 'gender'
        return t['ask_gender']
        
    elif step == 'gender':
        gen = 'Male'
        if any(w in msg for w in ['female', 'woman', 'girl', 'mahila', 'aurat', 'stree', 'பெண்', 'ஆண் இல்லை']):
            gen = 'Female'
        elif any(w in msg for w in ['male', 'man', 'boy', 'purush', 'aadmi', 'ஆண்']):
            gen = 'Male'
            
        session_state['gender'] = gen
        session_state['step'] = 'completed'
        
        # We now screen eligibility locally using the collected parameters
        user_prof = {
            'age': session_state.get('age'),
            'income': session_state.get('income'),
            'occupation': session_state.get('occupation'),
            'gender': session_state.get('gender'),
            'states': 'All'
        }
        
        results = screen_eligibility(user_prof)
        if not results:
            return t['no_schemes']
            
        # Compile response
        res_text = f"{t['eligible_list']}\n"
        
        # Simple translation dict for demo schemes
        hi_dict = {
            "PM-KISAN": ("पीएम-किसान (PM-KISAN)", "₹6000 प्रति वर्ष की वित्तीय सहायता (Financial support of ₹6000/year)"),
            "PM Shram Yogi Maan-dhan (PM-SYM)": ("पीएम श्रम योगी मान-धन (PM-SYM)", "₹3000/महीने की पेंशन (Pension of ₹3000/month)"),
            "PM Ujjwala Yojana": ("पीएम उज्ज्वला योजना (PM Ujjwala)", "मुफ्त एलपीजी कनेक्शन (Free LPG gas connection)"),
            "Ayushman Bharat (PM-JAY)": ("आयुष्मान भारत (PM-JAY)", "₹5 लाख तक का स्वास्थ्य बीमा (Health insurance up to ₹5 Lakh)"),
            "MGNREGA": ("मनरेगा (MGNREGA)", "100 दिन के रोजगार की गारंटी (100 days of guaranteed wage employment)")
        }

        for i, s in enumerate(results[:3]):
            name_hi, ben_hi = hi_dict.get(s['name'], (s['name'], s['benefit']))
            
            if session_state.get('lang') == 'hi' or session_state.get('lang') == 'ta':
                # Bilingual output
                res_text += f"\n{i+1}. {name_hi}\n   - Benefit: {ben_hi}\n"
            else:
                res_text += f"\n{i+1}. {s['name']}\n   - Benefit: {s['benefit']}\n"
            
            
        res_text += f"\n{t['checklists']}\n"
        # Compile document checklist
        docs = set()
        for s in results[:3]:
            for doc in s['documents']:
                docs.add(doc)
        # Document translation dictionary
        doc_hi_dict = {
            "Aadhaar Card": "आधार कार्ड (Aadhaar Card)",
            "Active Bank Account Passbook": "सक्रिय बैंक खाता पासबुक (Active Bank Account)",
            "Bank Account details": "बैंक खाते का विवरण (Bank Account details)",
            "Bank Passbook linked with Aadhaar": "आधार से जुड़ी बैंक पासबुक (Bank Passbook linked with Aadhaar)",
            "Land Ownership document": "भूमि स्वामित्व दस्तावेज (Land Ownership document)",
            "Passport size photographs": "पासपोर्ट साइज फोटो (Passport size photographs)",
            "Job Card / Swachh Bharat Mission ID": "जॉब कार्ड / स्वच्छ भारत मिशन आईडी (Job Card)",
            "Recent passport size photographs (for Job Card)": "पासपोर्ट साइज फोटो (Passport size photographs)",
            "Age Proof": "आयु प्रमाण (Age Proof)",
            "Auto-debit Consent Form": "ऑटो-डेबिट सहमति फॉर्म (Auto-debit Consent Form)",
            "Nominee Details (Aadhaar and relation proof)": "नामिनी का विवरण (Nominee Details)",
            "Affidavit stating non-ownership of pucca house": "पक्का घर न होने का शपथ पत्र (Affidavit stating no pucca house)",
            "Family ID Card / PM-JAY Letter": "परिवार पहचान पत्र / पीएम-जय पत्र (Family ID Card / PM-JAY Letter)",
            "Income Certificate": "आय प्रमाण पत्र (Income Certificate)",
            "Ration Card (BPL/Priority Household)": "राशन कार्ड (BPL/Priority Household) (Ration Card)",
            "Land Ownership Documents (Khatauni/Patta)": "भूमि स्वामित्व दस्तावेज (Land Ownership Documents)",
            "Mobile Number linked with Aadhaar": "आधार से जुड़ा मोबाइल नंबर (Mobile Number linked with Aadhaar)",
            "Aadhaar Card of Applicant and adult family members": "आवेदक और वयस्क परिवार के सदस्यों का आधार कार्ड (Aadhaar of family members)",
            "BPL Ration Card (or state-equivalent BPL list)": "बीपीएल राशन कार्ड (BPL Ration Card)",
            "Bank Account details (with IFSC)": "बैंक खाते का विवरण IFSC के साथ (Bank Account details with IFSC)",
            "Address Proof (Electricity bill/Water bill/Ration card)": "पता प्रमाण (Address Proof)",
            "Birth Certificate of the Girl Child": "बालिका का जन्म प्रमाण पत्र (Birth Certificate of the Girl Child)",
            "Aadhaar Card of the Parent / Guardian": "माता-पिता/अभिभावक का आधार कार्ड (Aadhaar Card of Parent/Guardian)",
            "PAN Card of the Parent / Guardian": "माता-पिता/अभिभावक का पैन कार्ड (PAN Card of Parent/Guardian)",
            "Address Proof of the Parent / Guardian": "माता-पिता/अभिभावक का पता प्रमाण (Address Proof of Parent/Guardian)",
            "Savings Bank Account Passbook (with IFSC)": "बचत बैंक खाता पासबुक IFSC के साथ (Savings Bank Passbook with IFSC)",
            "Active Mobile Number": "सक्रिय मोबाइल नंबर (Active Mobile Number)",
            "Nomination details": "नामांकन विवरण (Nomination details)",
            "Land Ownership records (Khasra/Khatauni)": "भूमि स्वामित्व रिकॉर्ड खसरा/खतौनी (Land Ownership records)",
            "Savings Bank Account details": "बचत बैंक खाते का विवरण (Savings Bank Account details)",
            "Mobile Number": "मोबाइल नंबर (Mobile Number)"
        }
                
        for doc in sorted(docs):
            if session_state.get('lang') in ['hi', 'ta']:
                res_text += f" - {doc_hi_dict.get(doc, doc)}\n"
            else:
                res_text += f" - {doc}\n"
            
        res_text += t['footer']
        session_state['step'] = 'ask_process'
        
        if session_state.get('lang') in ['hi', 'ta']:
            res_text += "\n\nक्या आप आवेदन प्रक्रिया के बारे में जानना चाहते हैं? (Yes/No) / Do you want to know the application process?"
        else:
            res_text += "\n\nDo you want to know the application process? (Yes/No)"
        return res_text
        
    elif step == 'ask_process':
        msg_lower = msg.strip().lower()
        if msg_lower in ['yes', 'ha', 'haan', 'y', 'हाँ', 'ஆம்', 'am']:
            session_state['step'] = 'post_flow_qna'
            process_text = "Here is the general application process:\n1. Gather all required documents listed above.\n2. Visit your nearest Common Service Centre (CSC) or Gram Panchayat.\n3. Ask the operator to fill out the scheme forms via the state or central e-District portal.\n4. Keep the application reference number for tracking."
            if session_state.get('lang') in ['hi', 'ta']:
                process_text += "\n\n(आवेदन प्रक्रिया: 1. सभी दस्तावेज जमा करें। 2. नजदीकी सीएससी (CSC) या पंचायत जाएं। 3. ऑपरेटर से फॉर्म भरवाएं।)"
            process_text += "\n\nDo you have any other questions? Ask me anything!"
            return process_text
        else:
            session_state['step'] = 'post_flow_qna'
            prompt = "Okay! Do you have any other questions? Ask me anything!"
            if session_state.get('lang') in ['hi', 'ta']:
                prompt = "ठीक है! क्या आपका कोई और सवाल है? आप कुछ भी पूछ सकते हैं! / " + prompt
            return prompt

        
    elif step == 'post_flow_qna':
        # Post-flow Q&A state using DuckDuckGo search
        if user_message.strip().lower() in ['restart', 'reset', 'start over']:
            session_state.clear()
            session_state['step'] = 'lang'
            return t['greet']
            
        search_context = perform_web_search(f"India welfare schemes {user_message}")
        if search_context:
            # If no Gemini, we just return the search context cleanly formatted.
            # (If Gemini is enabled, get_nlu_response will handle this state and use the context)
            response = f"Here is some information I found regarding your question:\n\n{search_context}\n(Type 'restart' to screen another person.)"
            return response
        else:
            return "I couldn't find an exact answer to that right now. Please check the official portal or your local Panchayat. (Type 'restart' to screen another person.)"

    elif step == 'completed':
        # Fallback if somehow ended up in completed
        session_state.clear()
        session_state['step'] = 'lang'
        return t['greet']
        
    return t['greet']

def get_nlu_response(user_message, session_state):
    """
    Main dialogue entry point.
    Determines if Gemini API is available. If yes, it screens eligibility
    locally to fetch context, then queries Gemini.
    If no API key, it uses the local rule-based NLU fallback.
    """
    # Force step start if session_state is empty
    if 'step' not in session_state:
        session_state['step'] = 'start'
        
    user_prof = {
        'age': session_state.get('age'),
        'income': session_state.get('income'),
        'occupation': session_state.get('occupation'),
        'gender': session_state.get('gender')
    }
    
    # Pre-screen eligible schemes to feed as context
    eligible_schemes = screen_eligibility(user_prof)
    
    if GEMINI_API_KEY:
        # We use Gemini RAG
        # If in Q&A state, or completed, or asking a question
        if session_state['step'] == 'post_flow_qna' or session_state['step'] == 'ask_process':
            search_context = perform_web_search(f"India welfare {user_message}")
            prompt = f"User profile: {json.dumps(user_prof)}. User asks: '{user_message}'.\nUse this search context to answer concisely and clearly:\n{search_context}\nIf the search context does not answer the question, use your general knowledge but advise checking official sources. Keep it brief. Provide instructions on document acquisition if asked."
            res = get_gemini_response(prompt, eligible_schemes)
            if res:
                return res
        elif session_state['step'] == 'completed' or 'question' in user_message.lower() or len(user_message) > 20:
            prompt = f"User profile details collected: {json.dumps(user_prof)}. User query/response: '{user_message}'. Dialogue Step: {session_state['step']}."
            res = get_gemini_response(prompt, eligible_schemes)
            if res:
                return res
                
    # Fallback to local NLU state machine
    return local_indic_fallback_nlu(user_message, session_state, eligible_schemes)
