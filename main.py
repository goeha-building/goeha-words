import time
import customtkinter
import sqlite3
import random
from typing import Callable, TypedDict, List, Any

# 변수
DB_NAME = "goeha_words.db"
TABLE_NAME = "words_table"

class WordDict(TypedDict):
    id: int | None  # SQLite는 id를 숫자로 준다능
    word: str
    meaning: str
    example: str | None
    hardness: int

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

class WordModal(customtkinter.CTkToplevel):
    def __init__(self, parent: Any, title: str = "단어 추가", on_confirm: Callable | None = None):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x250")
        self.grab_set()
        self.focus()
        self.on_confirm = on_confirm

        self.entry_eng = customtkinter.CTkEntry(self, placeholder_text="영어 단어")
        self.entry_eng.pack(pady=10, padx=20)
        self.entry_kor = customtkinter.CTkEntry(self, placeholder_text="한글 뜻")
        self.entry_kor.pack(pady=10, padx=20)
        self.entry_exa = customtkinter.CTkEntry(self, placeholder_text="예문")
        self.entry_exa.pack(pady=10, padx=20)

        self.btn_save = customtkinter.CTkButton(self, text="저장", command=self.save)
        self.btn_save.pack(pady=10)

    def save(self):
        word = self.entry_eng.get()
        meaning = self.entry_kor.get()
        example = self.entry_exa.get()
        # 뜻 정리 (공백 제거)
        clean_meaning = ",".join([m.strip() for m in meaning.split(",")])
        
        to_save = {
            "word": word,
            "meaning": clean_meaning,
            "example": example,
            "hardness": 0
        }
        if self.on_confirm:
            self.on_confirm(to_save)
        self.destroy()

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Goeha Words")
        self.geometry("800x500")
        
        # 1. 변수 초기화 (파이랜스 에러 방지용) app 실행하면서 샤워를 싹 해주는. 건가
        self.db = SqliteManager()
        self._word_manager = WordManager()
        self._words: List[Any] = []
        self.word_queue: List[Any] = []
        self.current_word: Any = None
        self.sw_running = False
        self.sw_counter = 0
        self.total_word_count = 0
        self.solved_count = 0
        self.wrong_count = 0

        # 2. DB 테이블 생성
        self.db.query(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT,
                meaning TEXT,
                example TEXT,
                hardness INTEGER
            )
        """)
        
        self._words = self._word_manager.get_all_words()

        # UI 배치
        self.grid_columnconfigure(0, weight=1)
        
        # 버튼
        self.button = customtkinter.CTkButton(self, text="단어추가", command=self.btn_callback_add_word)
        self.button.place(relx=0.05, rely=0.85, anchor="sw")
        self.button2 = customtkinter.CTkButton(self, text="리스트 수정", command=self.btn_callback_list_edit)
        self.button2.place(relx=0.05, rely=0.75, anchor="sw")


        # 시계
        self.clock_label = customtkinter.CTkLabel(self, text="00:00:00", font=("Arial", 24, "bold"))
        self.clock_label.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        self.update_clock()

        # 스톱워치
        self.sw_label = customtkinter.CTkLabel(self, text="00:00.0", font=("Arial", 30, "bold"), text_color="#FF9900")
        self.sw_label.grid(row=4, column=1, padx=20, pady=5, sticky="e")
        self.btn_sw_start = customtkinter.CTkButton(self, text="Start", command=self.toggle_stopwatch, fg_color="green", hover_color="#2C571A")
        self.btn_sw_start.grid(row=5, column=1, padx=20, pady=5, sticky="e")
        self.btn_sw_reset = customtkinter.CTkButton(self, text="Reset", command=self.reset_stopwatch, fg_color="gray", hover_color="#424242")
        self.btn_sw_reset.grid(row=6, column=1, padx=20, pady=5, sticky="e")

        # 학습실 실행
        self.study_room()

    def study_room(self):
        self.study_frame = customtkinter.CTkFrame(self, corner_radius=15)
        self.study_frame.place(relx=0.5, rely=0.4, anchor="center", relwidth=0.5, relheight=0.5)
        
        self.progress = customtkinter.CTkProgressBar(self.study_frame)
        self.progress.set(0)
        self.progress.pack(pady=20, padx=20, fill="x")
        
        word_count = len(self._words)
        self.word_label = customtkinter.CTkLabel(self.study_frame, text=f"현재 단어 수: {word_count}개", font=("Arial", 30, "bold"))
        self.word_label.pack(expand=True)
        
        self.interact = customtkinter.CTkEntry(self, placeholder_text="입력창")
        self.interact.place_forget()
        self.interact.bind("<Return>", lambda event: self.check_answer_logic())

        self.btn_start_study = customtkinter.CTkButton(self, text="학습 시작", command=self.start_study_ses)
        self.btn_start_study.place(relx=0.5, rely=0.9, anchor="center")

    def start_study_ses(self):
        self.interact.place(relx=0.5, rely=0.8, anchor="center", relwidth=0.4)
        self.word_queue = self._words.copy()
        random.shuffle(self.word_queue)
        self.total_word_count = len(self.word_queue)
        self.solved_count = 0
        self.wrong_count = 0
        self.btn_start_study.configure(text="확인", command=self.check_answer_logic)
        self.show_next_word()

    def show_next_word(self):
        if self.word_queue:
            self.current_word = self.word_queue.pop(0)
            self.word_label.configure(text=self.current_word["word"], text_color="black")
            self.interact.delete(0, 'end')
        else:
            self.interact.place_forget()
            res = f"🎉 학습 완료!\n틀린 횟수: {self.wrong_count}"
            self.word_label.configure(text=res, text_color="green")
            self.btn_start_study.configure(text="다시 시작", command=self.study_room)

    def check_answer_logic(self):
        if not self.current_word: return
        user_input = self.interact.get().strip()
        if not user_input: return

        user_answers = [a.strip() for a in user_input.split(",") if a.strip()]
        correct_meanings = [m.strip() for m in self.current_word["meaning"].split(",")]

        is_correct = all(ans in correct_meanings for ans in user_answers)
        
        if is_correct and user_answers:
            self.solved_count += 1
            self.progress.set(self.solved_count / self.total_word_count)
            self.show_next_word()
        else:
            self.wrong_count += 1
            self.word_label.configure(text=f"응 아니야\n정답: {self.current_word['meaning']}", text_color="red")
            insert_pos = random.randint(0, len(self.word_queue)) if self.word_queue else 0
            self.word_queue.insert(insert_pos, self.current_word)
            self.interact.delete(0, 'end')

    def toggle_stopwatch(self):
        if self.sw_running:
            self.sw_running = False
            self.btn_sw_start.configure(text="Start", fg_color="green", hover_color="#")
        else:
            self.sw_running = True
            self.btn_sw_start.configure(text="Stop", fg_color="red", hover_color="#AC0836")
            self.update_stopwatch()

    def reset_stopwatch(self):
        self.sw_running = False
        self.sw_counter = 0
        self.sw_label.configure(text="00:00.0")
        self.btn_sw_start.configure(text="Start", fg_color="green", hover_color="#2C571A")

    def update_stopwatch(self):
        if self.sw_running:
            self.sw_counter += 1
            total_seconds = self.sw_counter // 10
            deciseconds = self.sw_counter % 10
            minutes, seconds = divmod(total_seconds, 60)
            self.sw_label.configure(text=f"{minutes:02d}:{seconds:02d}.{deciseconds}")
            self.after(100, self.update_stopwatch)

    def btn_callback_add_word(self):
        WordModal(self, title="단어 추가", on_confirm=self.add_word_to_db)

    def btn_callback_list_edit(self):
        print("리스트 수정하기!")

    def add_word_to_db(self, data):
        self.db.insert(TABLE_NAME, data)
        self._words = self._word_manager.get_all_words()
        print("✅ DB 저장 완료!")

    def update_clock(self):
        self.clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

if __name__ == "__main__":
    app = App()
    app.mainloop()