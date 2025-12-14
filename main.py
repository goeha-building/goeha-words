import tkinter as tk
import customtkinter

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("700x500")

        self.button = customtkinter.CTkButton(self, text="my button", command=self.button_callbck)
        self.button.pack(padx=20, pady=20)

        self.button2 = customtkinter.CTkButton(self, text="my button", command=self.button_callbck)
        self.button2.pack(padx=20, pady=20)


    def button_callbck(self):
        print("button clicked")


def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()


