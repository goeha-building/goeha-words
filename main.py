import time
import customtkinter
import sqlite3
from typing import Callable, TypedDict, List


# 변수
DB_NAME = "goeha_words.db"
TABLE_NAME = "words_table"


# TODO WordDict의 스키마 정하기
class WordDict(TypedDict):
    id: str | None
    word: str
    meaning: str
    example: str | None
    hardness: int


# 바-이브-로-만든ㄻ
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

    def close(self):
        self.conn.close()

    def insert(self, table, data: dict):
        """
        사용법: db.insert("words", {"english": "Apple", "korean": "사과"})
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        try:
            self.cursor.execute(sql, tuple(data.values()))
            self.conn.commit()
            return self.cursor.lastrowid  # 방금 생긴 ID 반환
        except Exception as e:
            print(f"❌ Insert 에러: {e}")
            self.conn.rollback()

    def get_all(self, table, where: dict | None = None):
        """
        사용법:
        - 전체 조회: db.get_all("words")
        - 조건 조회: db.get_all("words", {"english": "Apple"})
        """
        sql = f"SELECT * FROM {table}"
        values = ()

        if where:
            # {"id": 1, "name": "kim"} -> "id=? AND name=?"
            conditions = [f"{k}=?" for k in where.keys()]
            sql += " WHERE " + " AND ".join(conditions)
            values = tuple(where.values())

        self.cursor.execute(sql, values)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_one(self, table, where: dict):
        """
        사용법: db.get_one("words", {"id": 1})
        """
        results = self.get_all(table, where)
        return results[0] if results else None

    def update(self, table, data: dict, where: dict):
        """
        사용법: db.update("words", {"korean": "풋사과"}, {"english": "Apple"})
        (Apple인 행의 korean을 풋사과로 변경)
        """
        # "korean=?" 같은 셋팅 구문 만들기
        set_clause = ", ".join([f"{k}=?" for k in data.keys()])
        where_clause = " AND ".join([f"{k}=?" for k in where.keys()])

        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        values = tuple(data.values()) + tuple(where.values())

        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
            return self.cursor.rowcount  # 바뀐 행 개수 반환
        except Exception as e:
            print(f"❌ Update 에러: {e}")
            self.conn.rollback()

    def delete(self, table, where: dict):
        """
        사용법: db.delete("words", {"id": 3})
        """
        where_clause = " AND ".join([f"{k}=?" for k in where.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"

        try:
            self.cursor.execute(sql, tuple(where.values()))
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            print(f"❌ Delete 에러: {e}")
            self.conn.rollback()

    # 복잡한 쿼리용 (여전히 필요할 때가 있음)
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

    def get_all_words(self):
        return self.sq_manager.get_all(TABLE_NAME)

    def save_word(self, word: WordDict):
        word["hardness"] = -1

        self.sq_manager.insert(
            table=TABLE_NAME,
            data=dict(word),
        )


class WordModal(customtkinter.CTkToplevel):
    def __init__(
        self,
        parent: customtkinter.CTk,
        title: str = "단어 추가",
        on_confirm: Callable | None = None,
    ):
        super().__init__(parent)
        self.title(title)

        # 모달 자1식 창 크기
        self.geometry("300x200")

        # 부1모 창 클릭 안되게 하는 코드입니다!
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
        meaning= self.entry_kor.get()
        example = self.entry_exa.get()
        to_save: WordDict = {
            "word": word,
            "meaning": meaning,
            "example": example
        }
            # 부1모 창에서 넘겨준 함수 실행 (데이터 전달)
        if self.on_confirm:
            self.on_confirm(to_save)
        self.destroy()  # 창 닫기


class App(customtkinter.CTk):
    _words = List[WordDict]
    _word_manager = WordManager()

    def __init__(self):
        super().__init__()
        self.geometry("700x500")
        self.db = SqliteManager()
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
        self._word_manager = WordManager()
        self._words = self._word_manager.get_all_words()
        print(self._words)

        self.grid_columnconfigure(0, weight=1)
        for index, word in enumerate(self._words):
            temp_label = customtkinter.CTkLabel(
                self,
                text=f"{word["word"]}",
                
                font=("Arial", 24, "bold"),
            )
            shit = word["meaning"].split(",")
            print(shit)
            temp_label.grid(
                row=index,
                column=0,
                padx=20,
                pady=(20, 10),
                sticky="w",
            )

        self.button = customtkinter.CTkButton(
            self, text="단어추가", command=self.btn_callback_add_word
        )

        self.button2 = customtkinter.CTkButton(
            self, text="리스트 수정", command=self.btn_callback_list_edit
        )
        # 시계
        self.clock_label = customtkinter.CTkLabel(
            self, text="00:00:00", font=("Arial", 24, "bold")  # 폰트 크기 24, 굵게
        )
        self.clock_label.grid(
            row=0,
            column=1,
            padx=20,
            pady=(20, 10),
            sticky="e",
        )

        self.button.grid(
            row=1,
            column=1,
            padx=20,
            pady=20,
            sticky="e",
        )
        self.button2.grid(
            row=2,
            column=1,
            padx=20,
            pady=20,
            sticky="e",
        )
        self.update_clock()
        # self.separator.grid(row=3, column=1, padx=20, pady=(20, 5), sticky="e")

        # 스톱워치 ui
        self.sw_label = customtkinter.CTkLabel(
            self, text="00:00.0", font=("Arial", 30, "bold"), text_color="#FF9900"
        )
        self.sw_label.grid(row=4, column=1, padx=20, pady=5, sticky="e")

        self.btn_sw_start = customtkinter.CTkButton(
            self, text="Start", command=self.toggle_stopwatch, fg_color="green"
        )
        self.btn_sw_start.grid(row=5, column=1, padx=20, pady=5, sticky="e")

        self.btn_sw_reset = customtkinter.CTkButton(
            self, text="Reset", command=self.reset_stopwatch, fg_color="gray"
        )
        self.btn_sw_reset.grid(row=6, column=1, padx=20, pady=5, sticky="e")
        self.reset_stopwatch()
        self.study_room()
        
    #여기는 나의 구역...엄청난 연구가 자행되고잇읍니다.
    def study_room(self):
        self.study_frame = customtkinter.CTkFrame(self, corner_radius=15)
        self.study_frame.place(relx=0.5, rely=0.4, anchor="center", relwidth=0.6, relheight=0.6)
        
        self.progress = customtkinter.CTkProgressBar(self.study_frame)
        self.progress.set(0)
        self.progress.pack(pady=20, padx=20, fill="x")
        
        word_count = len(self._words)
        self.word_label = customtkinter.CTkLabel(
            self.study_frame, 
            text=f"현재 단어 수: {word_count}개", 
            font=("Arial", 30, "bold")
        )
        self.word_label.pack(expand=True) # True는 대문자로!
        
        self.interact = customtkinter.CTkEntry(self, placeholder_text="뜻 입력해")
        self.interact.place(relx=0.5, rely=0.8, anchor="center", relwidth=0.4)
        # 엔터키 누르면 채점 로직 실행
        self.interact.bind("<Return>", lambda event: self.check_answer_logic())

        self.btn_start_study = customtkinter.CTkButton(
            self, text="학습 시작", command=self.start_study_ses
        )
        self.btn_start_study.place(relx=0.5, rely=0.9, anchor="center")

    def start_study_ses(self):
        import random
        self.word_queue = self._words.copy() # 이름을 word_queue로 통일
        random.shuffle(self.word_queue)
        self.total_word_count = len(self.word_queue)
        self.solved_count = 0
        
        # 버튼의 기능을 '확인'으로 변경
        self.btn_start_study.configure(text="확인", command=self.check_answer_logic)
        self.show_next_word()

    def show_next_word(self):
        if self.word_queue:
            self.current_word = self.word_queue.pop(0)
            self.word_label.configure(text=self.current_word["word"], text_color="black") # 글자색 초기화
            self.interact.delete(0, 'end') 
        else:
            self.word_label.configure(text="🎉 학습 완료!", text_color="green")
            self.btn_start_study.configure(text="학습 시작", command=self.start_study_ses)

    def check_answer_logic(self):
        user_input = self.interact.get().strip()
        if not user_input: return

        user_answers = [a.strip() for a in user_input.split(",") if a.strip()]
        correct_meanings = [m.strip() for m in self.current_word["meaning"].split(",")]

        is_correct = True
        for answer in user_answers:
            if answer not in correct_meanings:
                is_correct = False
                break
        
        if is_correct and user_answers:
            # 정답일 때
            self.solved_count += 1
            progress_value = self.solved_count / self.total_word_count
            self.progress.set(progress_value)
            self.show_next_word()
        else:
            # 오답일 때
            self.word_label.configure(
                text=f"응 아니야\n정답: {self.current_word['meaning']}", 
                text_color="red"
            )
            # 틀린 단어를 뭉치 중간에 다시 넣기
            import random
            # 남은 카드들 사이의 랜덤한 위치 계산
            insert_pos = random.randint(0, len(self.word_queue)) if self.word_queue else 0
            self.word_queue.insert(insert_pos, self.current_word)
            
            # 틀렸을 때는 바로 다음 단어로 넘어가지 않고, 
            # 사용자가 정답을 확인한 후 다시 '확인' 버튼을 누르면 넘어가게 하면 좋겟누
            self.interact.delete(0, 'end')
   
        
        

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

            time_str = f"{minutes:02d}:{seconds:02d}.{deciseconds}"
            self.sw_label.configure(text=time_str)

            self.after(100, self.update_stopwatch)


    def btn_callback_add_word(self):
        print("단어추가!")
        WordModal(self, title="단어 추가", on_confirm=self.add_word_to_db)

    def btn_callback_list_edit(self):
        print("리스트 수정하기!")

    def button_callbck(self):
        print("button clicked")

    def add_word_to_db(self, data):
        print(f"모달에서 받은 데이터: {data}")

        # DB에 저장
        self.db.insert(TABLE_NAME, data)
        self._words = self._word_manager.get_all_words()
        print("✅ DB 저장 완료!")

    def update_clock(self):
        current_time = time.strftime("%H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.after(1000, self.update_clock)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
