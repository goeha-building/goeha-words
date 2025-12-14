# GOEHA WORDS

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
```
