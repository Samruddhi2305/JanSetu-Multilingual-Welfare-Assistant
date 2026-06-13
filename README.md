# 🌉 JanSetu

### Multilingual Welfare Scheme Assistant for Rural India

> Bridging citizens to government welfare schemes through multilingual, low-bandwidth conversational AI.

---

## 🎯 Problem Statement

India operates more than **950 central and state welfare schemes**, yet millions of eligible citizens remain unaware of the benefits available to them.

Key challenges include:

* Language barriers
* Low digital literacy
* Complex documentation requirements
* Limited internet connectivity
* Lack of awareness regarding eligibility

As a result, many deserving beneficiaries fail to access schemes such as PM-KISAN, Ayushman Bharat, PM Ujjwala Yojana, PM-SYM, and others.

---

## 💡 Our Solution

**JanSetu** is a multilingual welfare assistance platform designed to help citizens:

✅ Discover welfare schemes they qualify for

✅ Understand eligibility criteria

✅ Receive required document checklists

✅ Access information in their preferred language

✅ Use low-bandwidth communication channels

The system is designed for deployment across:

* WhatsApp
* SMS
* Web
* IVR-based systems
* Missed-call triggered workflows

---

## ✨ Key Features

### 🌍 Multilingual Support

* English
* Hindi
* Tamil

### 🧠 Eligibility Screening Engine

Collects basic user information:

* Age
* Income
* Occupation
* Gender

and generates personalized scheme recommendations.

### 📄 Document Checklist Generation

Provides scheme-specific documentation requirements to simplify the application process.

### 📱 Low-Bandwidth Design

Optimized for users with limited connectivity and low-end devices.

### ☎️ Offline Fallback Workflow

Supports a missed-call based onboarding flow that can later continue over SMS.

### 🔒 Hallucination Reduction

Uses a structured welfare scheme database and rule-based retrieval before generating responses.

---

## 👥 Supported User Personas

### 🚜 Farmer

* Language: Hindi / Hinglish
* Example Schemes:

  * PM-KISAN
  * PM-KMY

### 🛵 Gig Worker

* Language: Tamil / Tanglish
* Example Schemes:

  * PM-SYM

### 👩 Woman Head of Household

* Language: Hindi
* Example Schemes:

  * PM Ujjwala Yojana

---

## 🏗️ System Architecture

```text
User
   │
   ▼
Multilingual Chat Interface
   │
   ▼
FastAPI Backend
   │
   ├── Eligibility Engine
   │
   ├── Scheme Database
   │
   ├── Gemini API (Optional)
   │
   └── Local Rule-Based NLU
   │
   ▼
Personalized Scheme Recommendations
   │
   ▼
Document Checklist & Guidance
```

---

## 🛠️ Tech Stack

| Category        | Technology                 |
| --------------- | -------------------------- |
| Backend         | FastAPI                    |
| Language        | Python                     |
| AI Model        | Gemini API                 |
| Fallback Engine | Rule-Based NLU             |
| Frontend        | HTML, CSS, JavaScript      |
| Search          | DuckDuckGo Search          |
| Deployment      | Google Colab + ngrok       |
| Data Storage    | JSON-based Scheme Database |

---

## 📂 Project Structure

```text
JanSetu-Multilingual-Welfare-Assistant
│
├── data/
│   ├── schemes.json
│   └── sessions.json
│
├── src/
│   ├── app.py
│   ├── llm.py
│   ├── search.py
│   └── session.py
│
├── static/
│   └── index.html
│
└── README.md
```

---

## 🚀 Running the Project

### 1. Clone Repository

```bash
git clone https://github.com/goelsuchet/JanSetu-Multilingual-Welfare-Assistant.git
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn requests pydantic duckduckgo-search
```

### 3. Run Application

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

### 4. Open Browser

```text
http://localhost:8000
```

---

## 📈 Expected Impact

If deployed in a district with approximately **10,000 target households**:

* Increased awareness of welfare schemes
* Higher enrollment rates
* Reduced documentation confusion
* Improved inclusion of low-literacy users
* Better last-mile delivery of government benefits

Even a modest increase in awareness can translate into significant financial benefits reaching underserved households.

---

## 🎥 Demo

A live demonstration and deployment notebook are included as part of the project submission.

---

## 👨‍💻 Team

**Team Welfare Wizards**

Developed as part of the AI & Intelligent Systems track for welfare accessibility and citizen empowerment.

---

### "Empowering every citizen with access to the benefits they deserve."

## 👨‍💻 Team Members

- Name 1 Suchet Goel
- Name 2 Samruddhi Diwase (@Samruddhi2305)
- Name 3 (@github_username)
- Name 4 (@github_username)

**Team Name:** Welfare Wizards 🪄
