import time
import customtkinter
import sqlite3
import random
import threading
import json
from typing import Callable, Tuple, TypedDict, List, Any
from PIL import Image

# Gemini API
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

# --- DB 매니저 (원본 유지) ---
class SqliteManager:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_name=DB_NAME):
        if hasattr(self, "initialized"): return
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.initialized = True

    def insert(self, table, data: dict):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        try:
            self.cursor.execute(sql, tuple(data.values()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
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
        if hasattr(self, "sq_manager"): return
        self.sq_manager = SqliteManager()
    def get_all_words(self) -> List[Any]:
        return self.sq_manager.get_all(TABLE_NAME)

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


# --- 단어 추가/수정 모달 (원본 유지) ---
class WordModal(customtkinter.CTkToplevel):
    def __init__(self, parent: Any, title: str = "단어 추가", on_confirm: Callable | None = None, word_data: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x300")
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
            if self.word_data.get("example"): self.entry_exa.insert(0, self.word_data["example"])

        self.btn_save = customtkinter.CTkButton(self, text="저장", command=self.save)
        self.btn_save.pack(pady=10)

    def save(self):
        to_save = {"word": self.entry_eng.get(), "meaning": self.entry_kor.get(), "example": self.entry_exa.get(), "hardness": self.word_data["hardness"] if self.word_data else 0}
        if self.word_data: to_save["id"] = self.word_data["id"]
        if self.on_confirm: self.on_confirm(to_save)
        self.destroy()

# --- 메인 앱 (모든 원본 기능 통합) ---
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Goeha Words (Full Edition)")
        self.geometry("900x600")

        # 데이터 및 설정
        self.db = SqliteManager()
        self._word_manager = WordManager()
        self.sw_running = False
        self.sw_counter = 0
        self.focus_guard_on = False
        self.current_selected_word = None
        self.word_queue = []
        
        # DB 초기화
        self.db.query(f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} (id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT, meaning TEXT, example TEXT, hardness INTEGER DEFAULT 0)")
        self.db.query(f"CREATE TABLE IF NOT EXISTS {KEY_TABLE_NAME} (id INTEGER PRIMARY KEY AUTOINCREMENT, api_key TEXT)")
        self.init_ai_system()
        # UI 배치
        self.setup_ui()
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


    def setup_ui(self):
        # 배경 이미지 (생략 가능)
        try:
            bg_data = Image.open("background3.jpg")
            self.bg_image = customtkinter.CTkImage(bg_data, bg_data, size=(900, 600))
            self.bg_label = customtkinter.CTkLabel(self, text="", image=self.bg_image)
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except: pass

        # 단어 리스트 (사이드바)
        self.word_list_frame = customtkinter.CTkScrollableFrame(self, width=200, height=350, label_text="내 단어장")
        self.word_list_frame.place(relx=0.02, rely=0.05)

        # 상세 정보 라벨
        self.info_label = customtkinter.CTkLabel(self, text="단어를 선택하세요", font=("Arial", 14), justify="left")
        self.info_label.place(relx=0.02, rely=0.7)

        # 버튼들
        self.btn_add = customtkinter.CTkButton(self, text="단어추가", width=100, command=self.btn_callback_add_word)
        self.btn_add.place(relx=0.02, rely=0.85)

        self.btn_del = customtkinter.CTkButton(self, text="삭제", width=60, fg_color="red", command=self.delete_word)
        self.btn_del.place(relx=0.02, rely=0.92)

        self.btn_mod = customtkinter.CTkButton(self, text="수정", width=60, command=self.btn_callback_modify_word, fg_color="red",)
        self.btn_mod.place(relx=0.1, rely=0.92)

        # 시계 및 스톱워치
        self.clock_label = customtkinter.CTkLabel(self, text="00:00:00", font=("Arial", 20, "bold"))
        self.clock_label.place(relx=0.98, rely=0.05, anchor="ne")
        self.update_clock()

        self.sw_label = customtkinter.CTkLabel(self, text="00:00.0", font=("Arial", 30, "bold"), text_color="#FF9900")
        self.sw_label.place(relx=0.98, rely=0.15, anchor="ne")
        customtkinter.CTkButton(self, text="Start/Stop", width=100, command=self.toggle_stopwatch).place(relx=0.98, rely=0.25, anchor="ne")

        # 알람 스위치
        self.switch_alert = customtkinter.CTkSwitch(self, text="깜짝 알림", command=self.toggle_focus_guard)
        self.switch_alert.place(relx=0.98, rely=0.35, anchor="ne")

        # 중앙 학습 영역
        self.study_frame = customtkinter.CTkFrame(self, corner_radius=15, width=600, height=500)
        self.study_frame.place(relx=0.5, rely=0.45, anchor="center")
        
        self.progress = customtkinter.CTkProgressBar(self.study_frame)
        self.progress.set(0)
        self.progress.pack(pady=20, padx=20, fill="x")

        self.word_label = customtkinter.CTkLabel(self.study_frame, text="준비 완료", font=("Arial", 35, "bold"))
        self.word_label.pack(expand=True)

        self.interact = customtkinter.CTkEntry(self, placeholder_text="뜻 입력 후 Enter", width=300)
        self.interact.place(relx=0.5, rely=0.7, anchor="center")
        self.interact.bind("<Return>", lambda e: self.check_answer_logic())

        customtkinter.CTkButton(self, text="전체 학습", command=lambda: self.start_study(False)).place(relx=0.5, rely=0.8, anchor="center")
        customtkinter.CTkButton(self, text="🔥 어려운 단어", fg_color="#C0392B", command=lambda: self.start_study(True)).place(relx=0.5, rely=0.88, anchor="center")
        customtkinter.CTkButton(self, text="작문 시험", fg_color="purple", command=lambda: WritingModal(self)).place(relx=0.5, rely=0.96, anchor="center")

    # --- 기능 함수들 (축약 없음) ---
    def refresh_word_list(self):
        for widget in self.word_list_frame.winfo_children(): widget.destroy()
        words = self._word_manager.get_all_words()
        for w in words:
            row = customtkinter.CTkFrame(self.word_list_frame, fg_color="transparent")
            row.pack(fill="x")
            # 어려운 단어 별표 버튼
            star_c = "#FFD700" if w['hardness'] == 1 else "gray"
            customtkinter.CTkButton(row, text="⭐", width=30, fg_color="transparent", text_color=star_c, command=lambda x=w: self.toggle_h(x)).pack(side="left")
            # 단어 버튼 (검은색 글씨 적용 포인트!)
            btn = customtkinter.CTkButton(row, text=w["word"], fg_color="transparent", text_color="black", anchor="w", command=lambda x=w: self.show_word_detail(x))
            btn.pack(side="left", fill="x", expand=True)

    def show_word_detail(self, word):
        self.current_selected_word = word
        detail = f"단어: {word['word']}\n뜻: {word['meaning']}\n예문: {word.get('example','')}"
        self.info_label.configure(text=detail)

    def toggle_h(self, word):
        new_v = 1 if word['hardness'] == 0 else 0
        self.db.query(f"UPDATE {TABLE_NAME} SET hardness=? WHERE id=?", (new_v, word['id']))
        self.refresh_word_list()

    def delete_word(self):
        if self.current_selected_word:
            self.db.query(f"DELETE FROM {TABLE_NAME} WHERE id=?", (self.current_selected_word['id'],))
            self.refresh_word_list()

    def btn_callback_add_word(self):
        WordModal(self, on_confirm=lambda d: [self.db.insert(TABLE_NAME, d), self.refresh_word_list()])

    def btn_callback_modify_word(self):
        if self.current_selected_word:
            WordModal(self, title="수정", word_data=self.current_selected_word, on_confirm=self.update_word)

    def update_word(self, data):
        wid = data.pop("id")
        cols = ", ".join([f"{k}=?" for k in data.keys()])
        self.db.query(f"UPDATE {TABLE_NAME} SET {cols} WHERE id=?", tuple(data.values()) + (wid,))
        self.refresh_word_list()

    # --- 학습 로직 (AI 삭제, 빠른 매칭) ---
    def start_study(self, hard_only):
        words = self._word_manager.get_all_words()
        self.word_queue = [w for w in words if w['hardness'] == 1] if hard_only else words.copy()
        if not self.word_queue: return
        random.shuffle(self.word_queue)
        self.total_q = len(self.word_queue)
        self.solved_q = 0
        self.show_next()

    def show_next(self):
        if self.word_queue:
            self.current_word = self.word_queue.pop(0)
            self.word_label.configure(text=self.current_word["word"], text_color="black")
            self.interact.delete(0, 'end')
        else:
            self.word_label.configure(text="🎉 완료!", text_color="green")

    def check_answer_logic(self):
        user_in = self.interact.get().strip()
        ans_list = [m.strip() for m in self.current_word["meaning"].split(",")]
        if user_in in ans_list:
            self.solved_q += 1
            self.progress.set(self.solved_q / self.total_q)
            self.show_next()
        else:
            self.word_label.configure(text=f"틀림! 정답: {self.current_word['meaning']}", text_color="red")
            self.word_queue.append(self.current_word)

    # --- 시계, 스톱워치, 알람 ---
    def update_clock(self):
        self.clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def toggle_stopwatch(self):
        self.sw_running = not self.sw_running
        if self.sw_running: self.update_sw()

    def update_sw(self):
        if self.sw_running:
            self.sw_counter += 1
            ts = self.sw_counter // 10
            self.sw_label.configure(text=f"{ts//60:02d}:{ts%60:02d}.{self.sw_counter%10}")
            self.after(100, self.update_sw)

    def toggle_focus_guard(self):
        self.focus_guard_on = self.switch_alert.get()
        if self.focus_guard_on: self.after(300000, self.alert_pop)

    def alert_pop(self):
        if self.focus_guard_on:
            win = customtkinter.CTkToplevel(self)
            win.attributes("-topmost", True)
            win.geometry("300x150")
            customtkinter.CTkLabel(win, text="🔥 집중하세요! 딴짓 금지!").pack(pady=20)
            customtkinter.CTkButton(win, text="네!", command=win.destroy).pack()
            self.after(300000, self.alert_pop)

if __name__ == "__main__":
    app = App()
    app.mainloop()