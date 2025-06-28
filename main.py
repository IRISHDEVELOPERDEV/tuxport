#!/usr/bin/env python3
# TuxPort - A Windows App Installer for Linux
# Licensed under the MIT License.
# © 2025 IRISHDEVELOPERDEV
# https://github.com/IRISHDEVELOPERDEV/tuxport

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import urllib.request
import tempfile
import re
import shutil
import sys

# --- Modern TuxPort UI with all features ---
print(f"TuxPort main.py is running from: {os.path.abspath(__file__)}", file=sys.stderr)

def is_wine_installed():
    try:
        subprocess.run(["wine", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

def prompt_install_wine():
    def open_terminal():
        terminal = shutil.which('gnome-terminal') or shutil.which('x-terminal-emulator')
        if terminal:
            subprocess.Popen([
                terminal, '--', 'bash', '-c',
                'echo "To install Wine, run:"; echo "sudo apt update && sudo apt install -y wine"; bash'
            ])
        else:
            messagebox.showinfo(
                "No Terminal Found",
                "Could not find a terminal emulator. Please open a terminal and run:\n\nsudo apt update && sudo apt install -y wine"
            )
    popup = tk.Toplevel(root)
    popup.title("Wine Required")
    popup.geometry("400x200")
    popup.resizable(False, False)
    ttk.Label(popup, text="Wine is not installed.\nTuxPort requires Wine to run Windows applications.", wraplength=380, anchor='center', justify='center').pack(pady=20)
    ttk.Label(popup, text="Would you like to open a terminal with the install command?", wraplength=380, anchor='center', justify='center').pack(pady=10)
    btn_frame = ttk.Frame(popup)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="Open Terminal", command=lambda: [open_terminal(), popup.destroy()]).pack(side='left', padx=10)
    ttk.Button(btn_frame, text="Cancel", command=popup.destroy).pack(side='left', padx=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

def show_about():
    about = tk.Toplevel(root)
    about.title("About TuxPort")
    about.geometry("480x320")  # Larger size
    about.resizable(False, False)
    about.configure(bg=BG, bd=0, highlightthickness=0)
    # Center the window, but keep it on screen
    about.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (480 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (320 // 2)
    y = max(0, y)
    x = max(0, x)
    about.geometry(f"+{x}+{y}")
    # Title label
    tk.Label(about, text="TuxPort", font=("Segoe UI", 20, "bold"), bg=BG, fg=ACCENT, anchor='center').pack(pady=(24, 8), fill='x')
    # Body text
    tk.Label(
        about,
        text="TuxPort is open source software.\nIt uses Wine (also open source) to run Windows applications on Linux.\n\nGitHub: github.com/IRISHDEVELOPERDEV/tuxport\n\u00a9 2025 IRISHDEVELOPERDEV\nLicensed under the MIT License.",
        font=("Segoe UI", 13),
        bg=BG,
        fg=FG,
        wraplength=420,
        justify='center',
        anchor='center'
    ).pack(pady=(0, 16), fill='x')
    # OK button
    ttk.Button(about, text="OK", command=about.destroy, style='TButton').pack(pady=16, fill='x', padx=60)
    about.transient(root)
    about.grab_set()
    root.wait_window(about)

def run_wine_installer():
    exe_path = filedialog.askopenfilename(
        title="Select a Windows Installer (.exe)",
        filetypes=[("Windows Executable", "*.exe")]
    )
    if exe_path:
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", "File does not exist.")
            return
        try:
            subprocess.run(["wine", exe_path], check=True)
        except FileNotFoundError:
            messagebox.showerror("Wine Not Found", "Wine is not installed or not in PATH.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to run installer.\n{e}")

def download_and_run():
    url = url_entry.get()
    if not url:
        if root.winfo_exists():
            messagebox.showerror("Invalid URL", "Please enter a URL.")
        return
    try:
        if url.lower().endswith('.exe'):
            exe_url = url
        else:
            from urllib.parse import urljoin
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            })
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8', errors='ignore')
            exe_links = re.findall(r'href=["\\\']([^"\\\']+\\.exe)["\\\']', html, re.IGNORECASE)
            if not exe_links:
                if root.winfo_exists():
                    messagebox.showerror("No .exe Found", "No .exe download links found on the page.")
                return
            exe_links = [urljoin(url, link) for link in exe_links]
            pick = pick_exe_link_dialog(exe_links)
            if pick is None:
                return
            exe_url = exe_links[pick]
        temp_dir = tempfile.gettempdir()
        local_filename = os.path.join(temp_dir, os.path.basename(exe_url))
        label.config(text="Downloading...")
        root.update()
        req = urllib.request.Request(exe_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        })
        with urllib.request.urlopen(req) as response, open(local_filename, 'wb') as out_file:
            out_file.write(response.read())
        label.config(text="Download complete. Running installer...")
        root.update()
        subprocess.run(["wine", local_filename], check=True)
        label.config(text="Select and run a Windows installer (.exe) using Wine.")
    except Exception as e:
        if root.winfo_exists():
            messagebox.showerror("Error", f"Failed to download or run installer.\n{e}")
        if root.winfo_exists():
            label.config(text="Select and run a Windows installer (.exe) using Wine.")

def pick_exe_link_dialog(links):
    if not root.winfo_exists():
        return None
    pick_win = tk.Toplevel(root)
    pick_win.title("Select .exe to Download")
    pick_win.geometry("800x500")  # Larger size
    # Center the window, but keep it on screen
    pick_win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (800 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (500 // 2)
    y = max(0, y)
    x = max(0, x)
    pick_win.geometry(f"+{x}+{y}")
    tk.Label(pick_win, text="Select a .exe to download and run:", font=("Segoe UI", 12, "bold")).pack(pady=16)
    listbox = tk.Listbox(pick_win, width=100, height=16)
    for link in links:
        listbox.insert(tk.END, link)
    listbox.pack(pady=12)
    result = {'index': None}
    def select():
        sel = listbox.curselection()
        if sel:
            result['index'] = sel[0]
            pick_win.destroy()
    select_btn = tk.Button(pick_win, text="Download Selected", command=select, font=("Segoe UI", 12, "bold"))
    select_btn.pack(pady=10)
    pick_win.transient(root)
    try:
        pick_win.grab_set()
        root.wait_window(pick_win)
    except tk.TclError:
        return None
    return result['index']

class EntryWithMenu(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Cut", command=self.cut)
        self.menu.add_command(label="Copy", command=self.copy)
        self.menu.add_command(label="Paste", command=self.paste)
        self.bind("<Button-3>", self.show_menu)
    def show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)
    def cut(self):
        self.event_generate('<<Cut>>')
    def copy(self):
        self.event_generate('<<Copy>>')
    def paste(self):
        self.event_generate('<<Paste>>')

# Unified dark mode colors
BG = "#23272e"
FG = "#e0e0e0"
ACCENT = "#4F8EF7"
LABEL = "#b0b0b0"
ENTRY_BG = "#2d313a"
ENTRY_FG = "#e0e0e0"
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 12)
FONT_DESC = ("Segoe UI", 10, "italic")
FONT_LABEL = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 12)

# --- Modern UI Setup ---
root = tk.Tk()
root.title("TuxPort – Windows App Installer for Linux")
root.configure(bg=BG)
# Let window size itself to content, but set a minimum size to avoid being too small
root.update_idletasks()
root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())

# --- Modern UI Setup (continued) ---
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=FONT_BUTTON, padding=10, foreground=FG, background=ACCENT)
style.map("TButton", background=[("active", ACCENT)])
style.configure("TLabel", background=BG, foreground=FG, font=FONT_LABEL)
style.configure("TFrame", background=BG)

# Main container for padding
container = ttk.Frame(root, padding=(32, 24, 32, 24), style='TFrame')
container.pack(fill='both', expand=True)

# Title and subtitle
header = ttk.Frame(container, style='TFrame')
header.pack(fill='x', pady=(0, 8))

title = tk.Label(header, text="TuxPort", font=FONT_TITLE, bg=BG, fg=ACCENT, anchor='center', justify='center')
title.pack(pady=(0, 2), fill='x')

subtitle = tk.Label(header, text="Open Source Windows App Installer for Linux", font=FONT_SUBTITLE, bg=BG, fg=LABEL, anchor='center', justify='center')
subtitle.pack(pady=(0, 10), fill='x')

# Description
desc = tk.Label(
    container,
    text="TuxPort is open source software.\nIt uses Wine (also open source) to run Windows applications on Linux.",
    font=FONT_DESC,
    bg=BG,
    fg=LABEL,
    justify="center",
    wraplength=440,
    anchor='center'
)
desc.pack(pady=(0, 18), fill='x')

# File install section
file_frame = ttk.Frame(container, style='TFrame')
file_frame.pack(fill='x', pady=(0, 10))

file_label = ttk.Label(file_frame, text="Select and run a Windows installer (.exe) using Wine.", style='TLabel', wraplength=440, anchor='center', justify='center')
file_label.pack(pady=(0, 8), fill='x')

def select_exe():
    exe = filedialog.askopenfilename(filetypes=[("Windows Executable", "*.exe")])
    if exe:
        messagebox.showinfo("Selected", f"You selected:\n{exe}")
        # TODO: Run with Wine

browse_btn = ttk.Button(file_frame, text="📁  Browse and Run .exe", command=select_exe, style='TButton')
browse_btn.pack(fill="x")

# URL input
url_frame = ttk.Frame(container, style='TFrame')
url_frame.pack(fill='x', pady=(18, 0))

url_label = ttk.Label(url_frame, text="Or enter a direct .exe download link:", style='TLabel', anchor='center', justify='center')
url_label.pack(pady=(0, 4), fill='x')

url_entry = ttk.Entry(url_frame, width=54, font=FONT_LABEL)
url_entry.pack(fill='x', ipady=6)

# Download button
download_btn = ttk.Button(container, text="⬇️  Download and Run .exe", style='TButton')
download_btn.pack(pady=18, fill="x")

# Bottom buttons
button_frame = ttk.Frame(container, style='TFrame')
button_frame.pack(pady=18, fill='x')

about_btn = ttk.Button(button_frame, text="About", command=show_about, style='TButton')
about_btn.pack(side="left", expand=True, fill='x', padx=(0, 10))

exit_btn = ttk.Button(button_frame, text="Exit", command=root.quit, style='TButton')
exit_btn.pack(side="left", expand=True, fill='x', padx=(10, 0))

# Make sure the button frame is visible and not cut off
button_frame.update_idletasks()
root.update_idletasks()

if not is_wine_installed():
    prompt_install_wine()

root.mainloop()
