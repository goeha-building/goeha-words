import time
import customtkinter
import sqlite3
import random
from typing import Callable, TypedDict, List, Any
from PIL import Image, ImageTk

# 변수
DB_NAME = "goeha_words.db"
TABLE_NAME = "words_table"

class WordDict(TypedDict):
    id: int | None
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
        if hasattr(self, "initialized"): return
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
        if hasattr(self, "sq_manager"): return
        self.sq_manager = SqliteManager()

    def get_all_words(self) -> List[Any]:
        return self.sq_manager.get_all(TABLE_NAME)

class WordModal(customtkinter.CTkToplevel):
    def __init__(self, parent: Any, title: str = "단어 추가", on_confirm: Callable | None = None, word_data: dict = None):
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
            self.entry_eng.insert(0, self.word_data['word'])
            self.entry_kor.insert(0, self.word_data['meaning'])
            if self.word_data.get('example'):
                self.entry_exa.insert(0, self.word_data['example'])

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
            "hardness": 0
        }
        if self.word_data:
            to_save["id"] = self.word_data["id"]
            
        if self.on_confirm:
            self.on_confirm(to_save)
        self.destroy()

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Goeha Words")
        self.geometry("800x500")
        
        # 배경 이미지 (없어도 오류 안 나게 처리)
        try:
            bg_image_data = Image.open("background3.jpg") 
            self.bg_image = customtkinter.CTkImage(light_image=bg_image_data, dark_image=bg_image_data, size=(800, 500))
            self.bg_label = customtkinter.CTkLabel(self, text="", image=self.bg_image)
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except:
            print("⚠️ 배경 이미지 로드 실패")

        # 변수쨩
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
        
        # DB 테이블 생성
        self.db.query(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT,
                meaning TEXT,
                example TEXT,
                hardness INTEGER
            )
        """)

        # UI 배치 (그리드 설정)
        self.grid_columnconfigure(0, weight=1)

        # 1. 단어 리스트
        self.word_list_frame = customtkinter.CTkScrollableFrame(self, width=150, height=255, label_text="내 단어장")
        self.word_list_frame.place(relx=0.05, rely=0.04, anchor="nw")

        # 2. 정보란/상작버튼/단어버튼
        self.info_label = customtkinter.CTkLabel(self, text="단어를 선택하십시오", font=("Arial", 16, "bold"))
        self.info_label.place(relx=0.05, rely=0.65, anchor="nw")

        self.delete_btn = customtkinter.CTkButton(self, text="삭제", fg_color="red", width=60)
        self.delete_btn.place(relx=0.05, rely=0.8, anchor="nw")
        
        self.modify_btn = customtkinter.CTkButton(self, text="수정", fg_color="red", width=60, command=self.btn_callback_modify_word)
        self.modify_btn.place(relx=0.05, rely=0.9, anchor="nw")

        self.button = customtkinter.CTkButton(self, text="단어추가", command=self.btn_callback_add_word)
        self.button.place(relx=0.15, rely=0.85, anchor="sw")
        
        self.button2 = customtkinter.CTkButton(self, text="리스트 수정", command=self.btn_callback_list_edit)
        self.button2.place(relx=0.15, rely=0.95, anchor="sw")

        # 3. 우측 상단 시계
        self.clock_label = customtkinter.CTkLabel(self, text="00:00:00", font=("Arial", 24, "bold"))
        self.clock_label.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        self.update_clock()

        # 4. 우측 하단 스톱워치 (살려냈습니다!)
        self.sw_label = customtkinter.CTkLabel(self, text="00:00.0", font=("Arial", 30, "bold"), text_color="#FF9900")
        self.sw_label.grid(row=4, column=1, padx=20, pady=5, sticky="e")
        self.btn_sw_start = customtkinter.CTkButton(self, text="Start", command=self.toggle_stopwatch, fg_color="green", hover_color="#2C571A")
        self.btn_sw_start.grid(row=5, column=1, padx=20, pady=5, sticky="e")
        self.btn_sw_reset = customtkinter.CTkButton(self, text="Reset", command=self.reset_stopwatch, fg_color="gray", hover_color="#424242")
        self.btn_sw_reset.grid(row=6, column=1, padx=20, pady=5, sticky="e")

        # 5. 중앙 학습실
        self.study_room()
        self.refresh_word_list()

    # --- 기능 함수들 ---

    def refresh_word_list(self):
        for widget in self.word_list_frame.winfo_children():
            widget.destroy()
        self._words = self._word_manager.get_all_words()
        for word_data in self._words:
            btn = customtkinter.CTkButton(
                self.word_list_frame, text=word_data["word"], fg_color="transparent", 
                text_color=("black", "white"), anchor="w",
                command=lambda w=word_data: self.show_word_detail(w)
            )
            btn.pack(fill="x", padx=5, pady=2)
        if hasattr(self, 'word_label'):
            self.word_label.configure(text=f"현재 단어 수: {len(self._words)}개")

    def show_word_detail(self, word_data):
        self.current_selected_word = word_data
        detail_text = f"단어: {word_data['word']}\n뜻: {word_data['meaning']}"
        if word_data.get('example'):
            detail_text += f"\n예문: {word_data['example']}"
        self.info_label.configure(text=detail_text)
        self.delete_btn.configure(command=lambda: self.delete_word(word_data['id']))

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
            WordModal(self, title="단어 수정", on_confirm=self.update_word_in_db, word_data=self.current_selected_word)
        else:
            self.info_label.configure(text="수정할 단어를 선택하세요!")

    def update_word_in_db(self, data):
        word_id = data.pop("id")
        columns = ", ".join([f"{k}=?" for k in data.keys()])
        sql = f"UPDATE {TABLE_NAME} SET {columns} WHERE id=?"
        self.db.query(sql, tuple(data.values()) + (word_id,))
        self.refresh_word_list()
        self.info_label.configure(text="수정 완료!")

    # --- 스톱워치 로직 (살려냈습니다!) ---
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

    # --- 학습실 로직 ---
    def study_room(self):
        self.study_frame = customtkinter.CTkFrame(self, corner_radius=15)
        self.study_frame.place(relx=0.5, rely=0.4, anchor="center", relwidth=0.4, relheight=0.5)
        
        self.progress = customtkinter.CTkProgressBar(self.study_frame)
        self.progress.set(0)
        self.progress.pack(pady=20, padx=20, fill="x")
        
        self.word_label = customtkinter.CTkLabel(self.study_frame, text=f"현재 단어 수: {len(self._words)}개", font=("Arial", 30, "bold"))
        self.word_label.pack(expand=True)
        
        self.interact = customtkinter.CTkEntry(self, placeholder_text="뜻을 입력하고 엔터!")
        self.interact.place_forget()
        self.interact.bind("<Return>", lambda event: self.check_answer_logic())

        self.btn_start_study = customtkinter.CTkButton(self, text="학습 시작", command=self.start_study_ses)
        self.btn_start_study.place(relx=0.5, rely=0.9, anchor="center")

    def start_study_ses(self):
        if not self._words:
            self.word_label.configure(text="단어를 먼저 추가하세요!")
            return
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
            self.word_label.configure(text=self.current_word["word"], text_color=("black", "white"))
            self.interact.delete(0, 'end')
            self.interact.focus()
        else:
            self.interact.place_forget()
            res = f"🎉 학습 완료!\n틀린 횟수: {self.wrong_count}"
            self.word_label.configure(text=res, text_color="green")
            self.btn_start_study.configure(text="다시 시작", command=self.start_study_ses)

    def check_answer_logic(self):
        if not self.current_word: return
        user_input = self.interact.get().strip()
        if not user_input: return

        correct_meanings = [m.strip() for m in self.current_word["meaning"].split(",")]
        
        if user_input in correct_meanings:
            self.solved_count += 1
            self.progress.set(self.solved_count / self.total_word_count)
            self.show_next_word()
        else:
            self.wrong_count += 1
            self.word_label.configure(text=f"틀렸어요!\n정답: {self.current_word['meaning']}", text_color="red")
            self.word_queue.append(self.current_word) # 틀리면 다시 큐에 넣음
            self.interact.delete(0, 'end')

    def update_clock(self):
        self.clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def btn_callback_list_edit(self):
        print("리스트 수정 버튼 클릭됨")

if __name__ == "__main__":
    app = App()
    app.mainloop()