import customtkinter as ctk

ctk.set_appearance_mode("system")  # or "dark", "light"
ctk.set_default_color_theme("blue")  # optional

app = ctk.CTk()  # like tk.Tk()
app.geometry("400x300")
app.title("TuxPort")

label = ctk.CTkLabel(app, text="TuxPort - Run .exe on Linux")
label.pack(pady=10)

button = ctk.CTkButton(app, text="Browse .exe", command=lambda: print("Clicked"))
button.pack(pady=10)

app.mainloop()
