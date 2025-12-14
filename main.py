import tkinter as tk
import customtkinter


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("700x500")

        self.button = customtkinter.CTkButton(
            self, text="리스트 바꾸기", command=self.btn_callback_list_change
        )
        self.button.pack(padx=20, pady=20)

        self.button2 = customtkinter.CTkButton(
            self, text="리스트 수정", command=self.button_callbck
        )
        self.button2.pack(padx=20, pady=20)

    def btn_callback_list_change(self):
        print("리스트바꾸기!")

    def btn_callback_list_edit(self):
        print("리스트 수정하기!")

    def button_callbck(self):
        print("button clicked")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
