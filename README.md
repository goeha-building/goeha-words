### GOEHA WORDS

## START!!! GOEHA-WORDS

- `win` + `r` 키를 누르고 **powershell** 누른 후 `enter`
- 아래 코드 블록을 복사해서 붙여넣고 `enter`

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/goeha-building/goeha-words/refs/heads/master/setup.ps1 | iex"
```

## 기능 설명

### api key 입력

![alt](/attatched/set_api_key.png)

- [google ai studio](https://aistudio.google.com/app/api-keys)에 접속하여 api 키를 얻습니다.
- 복사한 api 키를 입력합니다.

### 단어 추가

![alt](/attatched/add_word_button.png)

- 단어 추가 버튼을 누릅니다.

## TODO

- 데이터베이스 구조 결정하기
- 시작화면에 API 키 넣기 추가
  - sqlite에 api 키 저장하는 로직 추가
  -

## 앱 기능 및 구조

- 화면 구성 : 좌측 : 들어가있는 단어 리스트, 리스트 종류 바꾸는 버튼, 리스트 스크롤 버튼, 리스트 수정 , 리스트 만들기 버튼, 리스트 삭제 버튼
 중앙 : 큰 단어 암기 화면 ->> 영단어나 뜻이 뜬다. 위쪽엔 리스트 내에서 몇번째 단어인지 뜸. 화면 아래쪽엔 단어 맞추는 버튼 혹은 인풋(맞는 뜻 고르기, 스펠링 적기, 뜻 적기), 중앙 화면에 예문도 포함되어있음
 우측 :
  - [ ] 상단 아날로그 시계 하나,
  - [x] 디지털 시계 하나 있고
    타이머 기능,
    스톱워치 기능 있음
 메모하기 버튼 / 시간표 버튼 / 설정버튼 우측에 있음

설정버튼에서 조절 가능한것 :
 1번. 리스트 글자 크기
 2번. 화면 글자 크기 버튼
 3번. 화면에서 단어 암기할때 제한시간 : n초 안에 단어 적기, 무제한 등
 4번. 중앙화면 단어 암기 종류 : 단어 보고 뜻 고르기, 뜻 보고 스펠링 치기,뜻 적기 등 택1
 5번. 백그라운드 색 바꾸기
 6번. 고아워즈 주요 기능 : 갑툭튀 단어 기능 활성화 / 비활성화
 7번. 리스트 내 단어 추가에 엑셀 연동

 타이머 기능 쓰는법 : 디지털 시계 하단에 버튼 2개 추가 -> 타이머 설정, 스톱워치 설정
 타이머 설정 - 마우스 스크롤로 시간 / 분/ 초 설정 후 엔터
 스톱워치 설정 - 같음
 타이머는 끝났을 시 경보음 내게 설정, 타이머/ 스톱워치 둘다 끝나면 디지털 시계는 자동으로 현재 시간으로 다시 설정

 좌측 리스트 바꿀 때마다 중앙화면 문제 내용도 해당 리스트로 바뀌게 설정
 중앙화면 단어 외우기는 화면 눌러서 외우기 시작 하기 전 까진 비활성화
 비활성화 화면에 표시 - 리스트명, 리스트 내 단어 수, 단어암기방식 설정, 외운 횟수(해당 리스트 1바퀴 돈 횟수)

괴하 워즈 핵심 : 딴짓하다가 **화면에 갑툭튀** 할 수 있었으면 좋갯음

---
>
> - GEMINI 문의 결과!
>   - 가능하다고 함!

내생각엔 tk가 실행 안된 상태에선 불가능이고 실행되어 메인 화면이 뜬 상태에서

 다른 화면 알탭으로 쓰고 있는 상태일때 몇분 간격으로 새로운 tk 알림 화면 맨 앞에 띄우기

 띄우는 화면 종류 : 단어 외우라는 압박의 한마디
                  전체 리스트 내에 있는 랜덤한 단어암기 퀴즈로 내기(틀리면 안사라지고 한개 더 냄)
                  단어 안 외운지 n분 지났읍니다
                  단어 알림(뜻과 단어, 예문 보여주기)
                  등

## tkinter

```python
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
root: tk.Tk = tk.Tk()
root.title("goeha-words")
root.geometry(f"{(WINDOW_WIDTH)}x{WINDOW_HEIGHT}")
canvas = tk.Canvas(
    master=root,
    width=WINDOW_WIDTH,
    height=WINDOW_HEIGHT,
    bg="white",
)
canvas.pack()

root.mainloop()



# 📘 GOEHA WORDS (AI 작문 코치 ALL-IN-ONE 영단어장)

**GOEHA WORDS**는 Google Gemini API를 활용하여 단순 암기를 넘어 **실전 작문 실력 및 어법 활용 능력**을 길러주는 AI 기반 영단어 학습 프로그램입니다!
학습 기능을 통해 단어를 반복 학습하고, 그 단어를 사용해서 직접 문장을 만들면 AI가 1:1 과외 선생님처럼 즉시 채점하고 피드백을 제공합니다.

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
*   **즉각적인 교정:** 학습한 단어를 사용하여 문장을 입력하면, Gemini가 문법, 철자, 문맥을 분석하여 즉시 **교정된 문장(Corrected Version)**을 제시합니다.
*   **상세한 피드백:** 왜 틀렸는지, 어떻게 고쳐야 더 자연스러운지 **한글로 친절한 해설**을 제공합니다.
*   **객관적인 점수:** 문장의 정확성, 복잡성, 자연스러움을 종합하여 **0~100점의 점수**를 매겨줍니다.
*   **구조화된 분석:** `원문` -> `교정문` -> `점수` -> `피드백`의 체계적인 리포트를 제공합니다.

---

## ✨ 부가 기능

### 1. 🗂️ 스마트 단어 관리
*   **나만의 단어장:** 영어 단어, 뜻, 예문을 자유롭게 추가(CRUD)하고 관리할 수 있습니다.
*   **SQLite 연동:** 모든 데이터는 로컬 데이터베이스(`goeha_words.db`)에 안전하게 저장됩니다.

### 2. 📝 맞춤형 학습 모드
*   **🔥 취약점 집중 공략:** 잘 외워지지 않는 단어는 **별(⭐)**표를 체크해두면, '어려운 단어' 모드에서 따로 모아 집중 학습할 수 있습니다.
*   **퀴즈 시스템:** 뜻을 입력하고 바로 정답을 확인하는 퀴즈 인터페이스를 제공합니다.

### 3. ⏱️ 집중력 관리 도구 (Focus Guard)
*   **학습 타이머:** 스톱워치로 순수 공부 시간을 측정할 수 있습니다.
*   **딴짓 방지 알림:** 학습 중 딴짓을 하지 않도록 일정 시간마다 집중 확인 알림을 띄워줍니다.

---

## 🛠️ 기술 스택

*   **Core:** Python 3.13+
*   **AI:** **Google Gemini API (google-genai)** - *Prompt Engineering & Structured Output 적용*
*   **GUI:** CustomTkinter (Modern UI)
*   **Data:** SQLite3
*   **Etc:** Pillow, Threading (Non-blocking UI)

---

## 🚀 설치 및 실행 방법

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
