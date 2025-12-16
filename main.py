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
    sq_manager: SqliteManager

    def __init__(self) -> None:
        self.sq_manager = SqliteManager()

    def save_word(self, word: WordDict):
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

        self.btn_save = customtkinter.CTkButton(self, text="저장", command=self.save)
        self.btn_save.pack(pady=10)

    def save(self):
        english = self.entry_eng.get()
        korean = self.entry_kor.get()

        if english and korean:
            # 부1모 창에서 넘겨준 함수 실행 (데이터 전달)
            if self.on_confirm:
                self.on_confirm({"english": english, "korean": korean})
            self.destroy()  # 창 닫기


class App(customtkinter.CTk):
    _words = List

    def __init__(self):
        super().__init__()
        self.geometry("700x500")

        self.db = SqliteManager()
        self.db.query(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english TEXT,
                korean TEXT
            )
        """
        )
        all_words = self.db.get_all(
            table=TABLE_NAME,
        )
        print(all_words)
        self.grid_columnconfigure(0, weight=1)

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

    # 여기서 부터 app에 쓸 함수 정의

    def save_word(
        self,
    ):
        print("단어추가 시작")

        pass

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
