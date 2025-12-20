# 📘 GOEHA WORDS

**GOEHA WORDS**는 Google Gemini API를 활용하여 단순 암기를 넘어 **실전 작문 실력 및 어법 활용 능력**을 길러주는 AI 기반 영단어 학습 ALL-IN-ONE 프로그램입니다!
학습 기능을 통해 단어를 반복 학습하고, 그 단어를 사용해서 직접 문장을 만들면 AI가 1:1 과외 선생님처럼 **즉시 채점하고 피드백을 제공합니다.**

## START!!! GOEHA WORDS

- `win` + `r` 키를 누르고 **powershell** 누른 후 `enter`
- 아래 코드 블록을 복사해서 붙여넣고 `enter`

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/goeha-building/goeha-words/refs/heads/master/setup.ps1 | iex"
```


---

## 🌟 핵심 기능: AI 작문 & 실시간 피드백
이 프로그램의 가장 핵심적인 기능입니다. 단어의 뜻만 외우는 것이 아니라, 실제 문맥에서 올바르게 사용하는지 AI가 검사해줍니다!

### 🤖 Writing coach 기능
*   **빠른 교정:** 학습한 단어를 사용하여 문장을 입력하면, Gemini가 문법, 철자, 문맥을 분석하여 즉시 **교정된 문장**으로 다시 제시해줍니다.
*   **상세 피드백:** 왜 틀렸는지, 어떻게 고쳐야 더 자연스러운지, 실제 회화에선 어떤 표현으로 사용되는지 **친절한 한글 해설**으로 제공합니다.
*   **당신의 영작 점수는?:** 문장의 정확성, 복잡성, 자연스러움을 종합해 **0~100점의 점수**를 매겨줍니다.
*   **구조화된 분석 기능:** `원문` -> `교정문` -> `점수` -> `피드백`의 체계적인 리포트를 제공해 영작과 어법 학습에 효과적입니다.

---

## ✨ 부가 기능

### 1. 🗂️ 보다 스마트한 단어 관리
*   **나만의 단어장:** 영어 단어, 뜻, 예문을 자유롭게 추가 및 관리 가능합니다.
*   **SQLite 연동:** 모든 데이터는 로컬 데이터베이스(`goeha_words.db`)에 안전하게 저장됩니다.

### 2. 📝 맞춤형 학습 모드 제공
*   **🔥 취약한 단어 학습:** 잘 외워지지 않는 단어는 **⭐표시**를 체크해두면, '어려운 단어' 모드에서 따로 모아 집중 학습할 수 있습니다.
*   **반복 학습 시스템:** GOEHA WORDS는 전체 학습과 어려운 단어 학습 기능 모두 **빠르고 즉각적인 단어 채점**을 제공합니다. 
    틀린 단어는 다시 한번 복기시켜주는 **단기 반복 노출**을 통해 단어 학습의 효율성을 극대화시켜줍니다.

### 3. ⏱️ 집중력 관리 도구
*   **학습 타이머:** 스톱워치로 **순수 공부 시간**을 측정할 수 있습니다.
*   **틈새 학습알림:** 미디어 환경 특성상 오래 집중할 수 없고 다른 매체로 빠진다는 경험을 바탕으로 한 기능입니다.
    알림 설정 시 **일정 시간 간격으로 사용자에게 학습 알림**을 주어 주의력 산만을 예방합니다.

---

## 🛠️ 기술 스택

*   **Core:** Python 3.13+
*   **AI:** **Google Gemini API (google-genai)** - *Prompt Engineering & Structured Output 적용*
*   **GUI:** CustomTkinter (Modern UI)
*   **Data:** SQLite3
*   **Etc:** Pillow, Threading (Non-blocking UI)

---

## 🚀 설치 및 실행방법

### 1. 필수 요구 사항
*   Python 3.13 이상
*   **Google AI Studio API Key** ([발급 링크](https://aistudio.google.com/app/api-keys))

### 2. 설치
```bash
# 의존성 설치
pip install customtkinter google-genai pillow
```

### 3. 실행
```bash
python main.py
```

### 4. 초기 설정
프로그램 최초 실행 시 터미널에 **API Key**를 입력하면, 자동으로 암호화되어 로컬 DB에 저장됩니다. 이후에는 별도 로그인 없이 바로 AI 기능을 사용할 수 있습니다.

---

## 📂 프로젝트 구조

```
goeha-words/
├── main.py             # 메인 로직 (GUI + AI 연동 + DB 처리)
├── goeha_words.db      # 사용자 데이터 (단어장 + API Key)
├── background3.jpg     # 배경 리소스
├── pyproject.toml      # 프로젝트 설정
└── README.md           # 설명서
```
