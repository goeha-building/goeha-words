import tkinter as tk

def main():
    print("Hello from goeha-words!")

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


if __name__ == "__main__":
    main()


