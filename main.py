import time
import customtkinter
import sqlite3
import random
import threading
import json
from typing import Callable, Tuple, TypedDict, List, Any
from PIL import Image


# 재미이 임포트
from google import genai
from google.genai import types

# 변수
DB_NAME = "goeha_words.db"
TABLE_NAME = "words_table"
KEY_TABLE_NAME = "key_table"


class WordDict(TypedDict):
    id: int | None
    word: str
    meaning: str
    example: str | None
    hardness: int


class GeminiGrader:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.model = "gemini-flash-lite-latest"
        except Exception as e:
            print(f"⚠️ GenAI 클라이언트 초기화 오류: {e}")
            self.client = None

    def check_meanings(self, word, user_meanings_list):
        if not self.client:
            return {"error": True, "msg": "API 키 오류 또는 초기화 실패"}

        # 프롬프트: JSON으로 달라고 명확히 요구
        input_text = f"""
        Word: {word}
        User's Answer: {str(user_meanings_list)}
        
        Check if the User's Answer allows the meaning of the Word(STRICT!).

        Return JSON format: {{ "correct": ["matched_meaning"], "wrong": ["wrong_meaning"], "meanings": ["korean_meaning", "korean_meaning"] }}
        """

        try:
            # 설정: 응답 타입을 JSON으로 강제함 (이게 핵심!)
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction="You are a strict Language teacher. Output ONLY JSON.",
            )

            response = self.client.models.generate_content(
                model=self.model, contents=input_text, config=config
            )

            # JSON 모드를 썼으므로 별도 파싱 없이 바로 json.loads 가능
            if response.text:
                result_dict = json.loads(response.text)
                return result_dict
            else:
                return {"error": True, "msg": "AI 응답이 비어있음"}

        except Exception as e:
            error_msg = str(e)
            print(f"❌ AI 채점 중 오류 상세: {error_msg}")

            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return {"error": True, "msg": "⚠️ 사용량 초과! (잠시 후 다시 시도)"}

            return {"error": True, "msg": "⚠️ AI 연결 오류 발생"}


class SqliteManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_name=DB_NAME):
        if hasattr(self, "initialized"):
            return
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.initialized = True
        print("✅ DB 매니저 로드 완료")

    def insert(self, table, data: dict):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        try:
            self.cursor.execute(sql, tuple(data.values()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"❌ Insert 에러: {e}")
            self.conn.rollback()

    def get_all(self, table, where: dict | None = None):
        sql = f"SELECT * FROM {table}"
        values = ()
        if where:
            conditions = [f"{k}=?" for k in where.keys()]
            sql += " WHERE " + " AND ".join(conditions)
            values = tuple(where.values())
        self.cursor.execute(sql, values)
        return [dict(row) for row in self.cursor.fetchall()]

    def query(self, sql, args=()):
        self.cursor.execute(sql, args)
        if sql.strip().upper().startswith("SELECT"):
            return [dict(row) for row in self.cursor.fetchall()]
        else:
            self.conn.commit()
            return self.cursor.lastrowid


class WordManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "sq_manager"):
            return
        self.sq_manager = SqliteManager()

    def get_all_words(self) -> List[Any]:
        return self.sq_manager.get_all(TABLE_NAME)


# WordDict 타입 예시 (상황에 맞게 수정)
# WordDict = Dict[str, str]


class WritingModal(customtkinter.CTkToplevel):
    def __init__(self, parent: Any, title: str = "작문시험"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x600")  # 결과를 보여줘야 하니 좀 더 크게 잡음
        self.grab_set()

        key_data = SqliteManager().get_all(table=KEY_TABLE_NAME)
        api_key = None

        if not key_data:
            print("-" * 50)
            print("aistudio api key를 입력하십시오.")
            print("키가 없다면 아래 링크에서 발급 및 확인이 가능합니다:")
            print("👉 https://aistudio.google.com/app/api-keys")
            print("-" * 50)
            input_key = input("API KEY: ").strip()

            SqliteManager().insert(table=KEY_TABLE_NAME, data={"api_key": input_key})
            api_key = input_key
        else:
            api_key = key_data[0]["api_key"]
        # Gemini 클라이언트 초기화
        self.client = genai.Client(api_key=api_key)
        self.model_id = (
            "gemini-3-flash-preview"  # 실제 존재하는 모델명으로 수정 (3는 아직...)
        )

        # 스크롤 가능한 프레임 생성 (단어가 많을 경우 대비)
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self, width=450, height=500
        )
        self.scroll_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # 단어 목록 가져오기 (WordManager가 있다고 가정)
        # words = WordManager().get_all_words()
        # 테스트용 임시 데이터
        words = WordManager().get_all_words()

        for word in words:
            self.render_word_test(word=word)

        self.btn_exit = customtkinter.CTkButton(
            self, text="닫기", command=self.exit_modal
        )
        self.btn_exit.pack(pady=10)

    def render_word_test(self, word: WordDict):
        # 단어 라벨
        word_label = customtkinter.CTkLabel(
            self.scroll_frame, text=f"단어: {word['word']}", font=("Arial", 16, "bold")
        )
        word_label.pack(pady=(10, 5), padx=20, anchor="w")

        # 입력창
        entry_user_writing = customtkinter.CTkEntry(
            self.scroll_frame,
            placeholder_text="이 단어를 사용하여 작문하세요.",
            width=400,
        )
        entry_user_writing.pack(pady=5, padx=20)

        # 결과 표시용 텍스트박스 (처음엔 숨김 처리하거나 작게)
        result_label = customtkinter.CTkTextbox(
            self.scroll_frame, width=400, height=100, activate_scrollbars=False
        )
        result_label.insert("0.0", "결과가 여기에 표시됩니다.")
        result_label.pack(pady=5, padx=20)
        result_label.configure(state="disabled")

        # 제출 버튼 (람다를 사용하여 현재 입력창의 값을 전달)
        btn_submit = customtkinter.CTkButton(
            self.scroll_frame,
            text="검사하기",
            command=lambda: self.start_analysis(
                word["word"], entry_user_writing, result_label
            ),
        )
        btn_submit.pack(pady=(5, 20), padx=20)

    def start_analysis(self, word, entry, result_widget):
        user_text = entry.get()
        if not user_text.strip():
            return

        # UI가 멈추지 않게 별도 쓰레드에서 Gemini 호출
        result_widget.configure(state="normal")
        result_widget.delete("0.0", "end")
        result_widget.insert("0.0", "분석 중...")
        result_widget.configure(state="disabled")

        thread = threading.Thread(
            target=self.run_gemini, args=(word, user_text, result_widget)
        )
        thread.start()

    def run_gemini(self, word, writing, result_widget):
        try:
            # 네가 만든 설정 그대로 적용
            config = types.GenerateContentConfig(
                # thinking_config=types.ThinkingConfig(thinking_level="HIGH"), # 필요시 활성화
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    required=["original", "corrected", "score", "feedback"],
                    properties={
                        "original": genai.types.Schema(
                            type=genai.types.Type.STRING,
                            description="The original text provided by the user.",
                        ),
                        "corrected": genai.types.Schema(
                            type=genai.types.Type.STRING,
                            description="The grammatically and contextually corrected version of the text.",
                        ),
                        "score": genai.types.Schema(
                            type=genai.types.Type.INTEGER,
                            description="A writing score from 0 to 100.",
                        ),
                        "feedback": genai.types.Schema(
                            type=genai.types.Type.STRING,
                            description="Short explanation of the corrections and word usage.",
                        ),
                    },
                ),
                system_instruction="""## Role
You are a precise writing evaluator. Your task is to analyze the user's writing based on a provided target word and provide a concise critique.

## Input Specification
You will receive input in the following JSON format:
{
  \"word\": \"string\",
  \"user_writing\": \"string\"
}

## Task Procedures
1. **Target Word Usage**: Verify if the \"word\" is used correctly in terms of part of speech, meaning, and context.
2. **Linguistic Analysis**: 
   - Check for grammatical errors (tense, agreement, articles, etc.).
   - Evaluate spelling and punctuation.
   - Analyze semantic clarity and natural flow (idiomatic usage).
3. **Correction**: Provide a corrected version of the sentence that sounds natural to a native speaker.
4. **Scoring**: Assign a score from 0 to 100 based on accuracy, complexity, and naturalness.
5. **Use Korean to feedback**

## Output Format
Return ONLY a JSON object with the following keys:
{
  \"original\": \"The user's input string\",
  \"corrected\": \"The corrected version of the writing\",
  \"score\": number,
  \"feedback\": \"A concise explanation of errors and usage of the word\"
}""",
            )

            prompt = f"Target word: {word}\nUser writing: {writing}"

            # 스트리밍 대신 일반 호출로 처리 (JSON 전체를 한 번에 받기 위함)
            response = self.client.models.generate_content(
                model=self.model_id, contents=prompt, config=config
            )

            # 결과 파싱 및 UI 업데이트
            res_data: Any = (
                response.parsed
            )  # Structured Output 덕분에 바로 객체로 들어옴
            output_text = f"{res_data}"

            self.update_result_ui(result_widget, output_text)

        except Exception as e:
            self.update_result_ui(result_widget, f"오류 발생: {str(e)}")

    def update_result_ui(self, widget, text):
        # 메인 쓰레드에서 UI 업데이트
        widget.configure(state="normal")
        widget.delete("0.0", "end")
        widget.insert("0.0", text)
        widget.configure(state="disabled")

    def exit_modal(self):
        self.destroy()


class WordModal(customtkinter.CTkToplevel):
    def __init__(
        self,
        parent: Any,
        title: str = "단어 추가",
        on_confirm: Callable | None = None,
        word_data: dict | None = None,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x250")
        self.grab_set()
        self.focus()
        self.on_confirm = on_confirm
        self.word_data = word_data

        self.entry_eng = customtkinter.CTkEntry(self, placeholder_text="영어 단어")
        self.entry_eng.pack(pady=10, padx=20)
        self.entry_kor = customtkinter.CTkEntry(self, placeholder_text="뜻")
        self.entry_kor.pack(pady=10, padx=20)
        self.entry_exa = customtkinter.CTkEntry(self, placeholder_text="예문")
        self.entry_exa.pack(pady=10, padx=20)

        if self.word_data:
            self.entry_eng.insert(0, self.word_data["word"])
            self.entry_kor.insert(0, self.word_data["meaning"])
            if self.word_data.get("example"):
                self.entry_exa.insert(0, self.word_data["example"])

        self.btn_save = customtkinter.CTkButton(self, text="저장", command=self.save)
        self.btn_save.pack(pady=10)

    def save(self):
        word = self.entry_eng.get()
        meaning = self.entry_kor.get()
        example = self.entry_exa.get()
        clean_meaning = ",".join([m.strip() for m in meaning.split(",")])

        to_save = {
            "word": word,
            "meaning": clean_meaning,
            "example": example,
            "hardness": 0,
        }
        if self.word_data:
            to_save["id"] = self.word_data["id"]

        if self.on_confirm:
            self.on_confirm(to_save)
        self.destroy()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Goeha Words (AI Edition)")
        self.geometry("800x500")

        # 배경 이미지
        try:
            bg_image_data = Image.open("background3.jpg")
            self.bg_image = customtkinter.CTkImage(
                light_image=bg_image_data, dark_image=bg_image_data, size=(800, 500)
            )
            self.bg_label = customtkinter.CTkLabel(self, text="", image=self.bg_image)
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except:
            print("⚠️ 배경 이미지 로드 실패")

        try:
            self.iconbitmap("icon.ico")
        except Exception as e:
            print(f"⚠️ 아이콘 로드 실패: {e}")

        # 변수
        self.db = SqliteManager()
        self._word_manager = WordManager()
        self._words = []
        self.word_queue = []
        self.current_word = None
        self.current_selected_word = None
        self.sw_running = False
        self.sw_counter = 0
        self.total_word_count = 0
        self.solved_count = 0
        self.wrong_count = 0
        self.gemini_grader = None

        # DB 테이블 생성
        self.db.query(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT,
                meaning TEXT,
                example TEXT,
                hardness INTEGER
            )
        """
        )
        self.db.query(
            f"""
            CREATE TABLE IF NOT EXISTS {KEY_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT
            )
        """
        )

        self.init_ai_system()

        # UI 배치
        self.grid_columnconfigure(0, weight=1)

        # 1. 단어 리스트
        self.word_list_frame = customtkinter.CTkScrollableFrame(
            self, width=150, height=255, label_text="내 단어장"
        )
        self.word_list_frame.place(relx=0.05, rely=0.04, anchor="nw")

        # 2. 정보란
        self.info_label = customtkinter.CTkLabel(
            self, text="단어를 선택하십시오", font=("Arial", 16, "bold")
        )
        self.info_label.place(relx=0.05, rely=0.65, anchor="nw")

        self.delete_btn = customtkinter.CTkButton(
            self, text="삭제", fg_color="red", width=60
        )
        self.delete_btn.place(relx=0.05, rely=0.8, anchor="nw")

        self.modify_btn = customtkinter.CTkButton(
            self,
            text="수정",
            fg_color="red",
            width=60,
            command=self.btn_callback_modify_word,
        )
        self.modify_btn.place(relx=0.05, rely=0.9, anchor="nw")

        self.button = customtkinter.CTkButton(
            self, text="단어추가", command=self.btn_callback_add_word
        )
        self.button.place(relx=0.15, rely=0.85, anchor="sw")

        self.button2 = customtkinter.CTkButton(
            self, text="리스트 수정", command=self.btn_callback_list_edit
        )
        self.button2.place(relx=0.15, rely=0.95, anchor="sw")

        # 3. 우측 상단 시계
        self.clock_label = customtkinter.CTkLabel(
            self, text="00:00:00", font=("Arial", 24, "bold")
        )
        self.clock_label.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        self.update_clock()

        # 4. 우측 하단 스톱워치
        self.sw_label = customtkinter.CTkLabel(
            self, text="00:00.0", font=("Arial", 30, "bold"), text_color="#FF9900"
        )
        self.sw_label.grid(row=4, column=1, padx=20, pady=5, sticky="e")
        self.btn_sw_start = customtkinter.CTkButton(
            self,
            text="Start",
            command=self.toggle_stopwatch,
            fg_color="green",
            hover_color="#2C571A",
        )
        self.btn_sw_start.grid(row=5, column=1, padx=20, pady=5, sticky="e")
        self.btn_sw_reset = customtkinter.CTkButton(
            self,
            text="Reset",
            command=self.reset_stopwatch,
            fg_color="gray",
            hover_color="#424242",
        )
        self.btn_sw_reset.grid(row=6, column=1, padx=20, pady=5, sticky="e")

        self.btn_writing_test = customtkinter.CTkButton(
            self,
            text="btn_writing_test",
            command=self.open_writing_test,
            fg_color="gray",
            hover_color="#424242",
        )
        self.btn_writing_test.grid(row=7, column=1, padx=20, pady=5, sticky="e")

        # 5. 중앙 학습실
        self.study_room()
        self.refresh_word_list()

    def init_ai_system(self):
        key_data = self.db.get_all(table=KEY_TABLE_NAME)
        api_key = None

        if not key_data:
            print("-" * 50)
            print("aistudio api key를 입력하십시오.")
            print("키가 없다면 아래 링크에서 발급 및 확인이 가능합니다:")
            print("👉 https://aistudio.google.com/app/api-keys")
            print("-" * 50)
            input_key = input("API KEY: ").strip()
            self.db.insert(table=KEY_TABLE_NAME, data={"api_key": input_key})
            api_key = input_key
        else:
            api_key = key_data[0]["api_key"]

        print(f"🔑 AI 초기화 시도... (Key: {api_key[:10]}...)")
        self.gemini_grader = GeminiGrader(api_key)

    # --- 기능 함수들 ---

    def refresh_word_list(self):
        for widget in self.word_list_frame.winfo_children():
            widget.destroy()
        self._words = self._word_manager.get_all_words()
        for word_data in self._words:
            btn = customtkinter.CTkButton(
                self.word_list_frame,
                text=word_data["word"],
                fg_color="transparent",
                text_color=("black", "white"),
                anchor="w",
                command=lambda w=word_data: self.show_word_detail(w),
            )
            btn.pack(fill="x", padx=5, pady=2)
        if hasattr(self, "word_label"):
            self.word_label.configure(
                text=f"현재 단어 수: {len(self._words)}개",
                text_color=("black", "white"),
            )

    def open_writing_test(self):
        WritingModal(self)

    def show_word_detail(self, word_data):
        self.current_selected_word = word_data
        detail_text = f"단어: {word_data['word']}\n뜻: {word_data['meaning']}"
        if word_data.get("example"):
            detail_text += f"\n예문: {word_data['example']}"
        self.info_label.configure(text=detail_text)
        self.delete_btn.configure(command=lambda: self.delete_word(word_data["id"]))

    def delete_word(self, word_id):
        self.db.query(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (word_id,))
        self.refresh_word_list()
        self.info_label.configure(text="삭제되었습니다.")

    def btn_callback_add_word(self):
        WordModal(self, title="단어 추가", on_confirm=self.add_word_to_db)

    def add_word_to_db(self, data):
        self.db.insert(TABLE_NAME, data)
        self.refresh_word_list()

    def btn_callback_modify_word(self):
        if self.current_selected_word:
            WordModal(
                self,
                title="단어 수정",
                on_confirm=self.update_word_in_db,
                word_data=self.current_selected_word,
            )
        else:
            self.info_label.configure(text="수정할 단어를 선택하세요!")

    def update_word_in_db(self, data):
        word_id = data.pop("id")
        columns = ", ".join([f"{k}=?" for k in data.keys()])
        sql = f"UPDATE {TABLE_NAME} SET {columns} WHERE id=?"
        self.db.query(sql, tuple(data.values()) + (word_id,))
        self.refresh_word_list()
        self.info_label.configure(text="수정 완료!")

    # --- 스톱워치 ---
    def toggle_stopwatch(self):
        if self.sw_running:
            self.sw_running = False
            self.btn_sw_start.configure(text="Start", fg_color="green")
        else:
            self.sw_running = True
            self.btn_sw_start.configure(text="Stop", fg_color="red")
            self.update_stopwatch()

    def reset_stopwatch(self):
        self.sw_running = False
        self.sw_counter = 0
        self.sw_label.configure(text="00:00.0")
        self.btn_sw_start.configure(text="Start", fg_color="green")

    def update_stopwatch(self):
        if self.sw_running:
            self.sw_counter += 1
            total_seconds = self.sw_counter // 10
            deciseconds = self.sw_counter % 10
            minutes, seconds = divmod(total_seconds, 60)
            self.sw_label.configure(text=f"{minutes:02d}:{seconds:02d}.{deciseconds}")
            self.after(100, self.update_stopwatch)

    # --- 학습실 ---
    def study_room(self):
        self.study_frame = customtkinter.CTkFrame(self, corner_radius=15)
        self.study_frame.place(
            relx=0.5, rely=0.4, anchor="center", relwidth=0.4, relheight=0.5
        )

        self.progress = customtkinter.CTkProgressBar(self.study_frame)
        self.progress.set(0)
        self.progress.pack(pady=20, padx=20, fill="x")

        self.word_label = customtkinter.CTkLabel(
            self.study_frame,
            text=f"현재 단어 수: {len(self._words)}개",
            font=("Arial", 30, "bold"),
        )
        self.word_label.pack(expand=True)

        self.interact = customtkinter.CTkEntry(
            self, placeholder_text="뜻을 입력하고 엔터!"
        )
        self.interact.place_forget()
        self.interact.bind("<Return>", lambda event: self.check_answer_logic())

        self.btn_start_study = customtkinter.CTkButton(
            self, text="학습 시작", command=self.start_study_ses
        )
        self.btn_start_study.place(relx=0.5, rely=0.9, anchor="center")

    def start_study_ses(self):
        if not self._words:
            self.word_label.configure(
                text="단어를 먼저 추가하세요!", text_color=("black", "white")
            )
            return
        self.interact.place(relx=0.5, rely=0.8, anchor="center", relwidth=0.4)
        self.word_queue = self._words.copy()
        random.shuffle(self.word_queue)
        self.total_word_count = len(self.word_queue)
        self.solved_count = 0
        self.wrong_count = 0
        self.btn_start_study.configure(
            text="제출 (Enter)", command=self.check_answer_logic
        )
        self.show_next_word()

    def show_next_word(self):
        if self.word_queue:
            self.current_word = self.word_queue.pop(0)
            self.word_label.configure(
                text=self.current_word["word"], text_color=("black", "white")
            )
            self.interact.delete(0, "end")
            self.interact.configure(state="normal")
            self.interact.focus()
        else:
            self.interact.place_forget()
            res = f"🎉 학습 완료!\n틀린 횟수: {self.wrong_count}"
            self.word_label.configure(text=res, text_color="green")
            self.btn_start_study.configure(
                text="다시 시작", command=self.start_study_ses
            )

    def check_answer_logic(self):
        if not self.current_word:
            return

        user_input = self.interact.get().strip()
        if not user_input:
            return

        # UI를 '채점 중' 상태로 변경
        self.word_label.configure(text="🤖 AI가 생각하는 중...", text_color="blue")
        self.interact.configure(state="disabled")

        # 스레드에서 AI 실행
        threading.Thread(target=self.run_ai_grading, args=(user_input,)).start()

    def run_ai_grading(self, user_input):
        # 1차적으로 정확한 텍스트 매칭 시도
        if self.current_word is None:
            return
        correct_meanings = [m.strip() for m in self.current_word["meaning"].split(",")]
        user_input_list = [m.strip() for m in user_input.split(",")]

        is_exact_match = False
        for u in user_input_list:
            if u in correct_meanings:
                is_exact_match = True
                break

        if is_exact_match:
            self.after(
                0, lambda: self.handle_result(True, user_input, "정확한 정답입니다!")
            )
            return

        # 2차적으로 AI에게 물어보기
        if self.gemini_grader:
            result = self.gemini_grader.check_meanings(
                self.current_word["word"], user_input_list
            )

            # AI 에러가 발생한 경우 (429 등)
            if result and "error" in result and result["error"]:
                self.after(0, lambda: self.handle_ai_error(result["msg"]))
                return

            # 정상 응답 처리
            if result and result.get("correct"):
                msg = f"AI 인정 정답: {', '.join(result['correct'])}"
                self.after(0, lambda: self.handle_result(True, user_input, msg))
            else:
                # 오답일 경우, AI가 알려준 meanings를 함께 전달
                ai_meanings = result.get("meanings", []) if result else []
                self.after(
                    0,
                    lambda: self.handle_result(
                        False, user_input, ai_meanings=ai_meanings
                    ),
                )
        else:
            self.after(0, lambda: self.handle_result(False, user_input))

    def handle_ai_error(self, error_msg):
        # 에러 발생 시 UI 처리
        self.word_label.configure(text=error_msg, text_color="#FF8C00")  # 주황색
        self.interact.configure(
            state="normal"
        )  # 입력창 다시 활성화 (사용자가 다시 시도하거나 기다릴 수 있게)
        # 큐에 다시 넣지 않고, 현재 화면에서 머무름

    def handle_result(self, is_correct, user_input, msg="", ai_meanings=None):
        self.interact.configure(state="normal")
        if self.current_word is None:
            return
        if is_correct:
            self.solved_count += 1
            self.progress.set(self.solved_count / self.total_word_count)
            if msg:
                print(msg)
            self.show_next_word()
        else:
            self.wrong_count += 1

            # AI가 알려준 뜻이 있으면 그것을 사용, 없으면(또는 리스트가 비었으면) DB값 사용
            if ai_meanings and len(ai_meanings) > 0:
                answer_display = ", ".join(ai_meanings)
            else:
                answer_display = self.current_word["meaning"]

            self.word_label.configure(
                text=f"틀렸어요!\n정답: {answer_display}",
                text_color="red",
            )
            self.word_queue.append(self.current_word)
            self.interact.delete(0, "end")
            self.interact.focus()

    def update_clock(self):
        self.clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def btn_callback_list_edit(self):
        print("리스트 수정 버튼 클릭됨")


if __name__ == "__main__":
    app = App()
    app.mainloop()
