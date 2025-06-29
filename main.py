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

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    dnd_available = True
except ImportError:
    dnd_available = False

def custom_file_explorer(initialdir=None):
    import pathlib
    import time
    explorer = tk.Toplevel(root)
    explorer.title("Select a Windows Installer (.exe)")
    explorer.geometry("700x450")
    explorer.resizable(True, True)

    selected_file = tk.StringVar()
    current_dir = tk.StringVar(value=initialdir or os.path.expanduser("~"))

    # Sidebar quick access (only show folders that exist)
    sidebar = tk.Frame(explorer, bg="#f0f0f0", width=120)
    sidebar.pack(side='left', fill='y')
    quick_folders = [
        ("🏠 Home", os.path.expanduser("~")),
        ("📄 Documents", os.path.join(os.path.expanduser("~"), "Documents")),
        ("⬇️ Downloads", os.path.join(os.path.expanduser("~"), "Downloads")),
        ("🎵 Music", os.path.join(os.path.expanduser("~"), "Music")),
        ("🖼️ Pictures", os.path.join(os.path.expanduser("~"), "Pictures")),
        ("🎬 Videos", os.path.join(os.path.expanduser("~"), "Videos")),
    ]
    for label, path in quick_folders:
        if os.path.exists(path):
            def go(p=path):
                current_dir.set(p)
                update_file_list(p)
            btn = tk.Button(sidebar, text=label, anchor='w', command=go, relief='flat', bg="#f0f0f0")
            btn.pack(fill='x', padx=8, pady=2)

    # Main area
    main_frame = tk.Frame(explorer)
    main_frame.pack(side='left', fill='both', expand=True)

    # Path and navigation
    nav_frame = tk.Frame(main_frame)
    nav_frame.pack(fill='x', pady=(8, 0))
    up_btn = tk.Button(nav_frame, text="⬆️ Up", command=lambda: on_up())
    up_btn.pack(side='left', padx=4)
    path_label = tk.Label(nav_frame, textvariable=current_dir, anchor='w')
    path_label.pack(side='left', fill='x', expand=True, padx=8)

    # Title/instructions
    title_label = tk.Label(main_frame, text="Select a Windows Installer (.exe) from the list below.", font=("Segoe UI", 12, "bold"), anchor='w')
    title_label.pack(fill='x', padx=8, pady=(8, 0))

    # Table headers
    header_frame = tk.Frame(main_frame)
    header_frame.pack(fill='x', padx=8)
    tk.Label(header_frame, text="Name", width=32, anchor='w', font=("Segoe UI", 10, "bold")).pack(side='left')
    tk.Label(header_frame, text="Size", width=10, anchor='w', font=("Segoe UI", 10, "bold")).pack(side='left')
    tk.Label(header_frame, text="Modified", width=18, anchor='w', font=("Segoe UI", 10, "bold")).pack(side='left')

    # File list
    file_list = tk.Listbox(main_frame, selectmode='single', font=("Segoe UI", 11), width=80, height=18)
    file_list.pack(fill='both', expand=True, padx=8, pady=4)

    # Status/empty message
    status_label = tk.Label(main_frame, text="", fg="#888", anchor='w')
    status_label.pack(fill='x', padx=8)

    def update_file_list(path):
        file_list.delete(0, tk.END)
        try:
            entries = sorted(pathlib.Path(path).iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            if not entries:
                status_label.config(text="(This folder is empty)")
            else:
                status_label.config(text="")
            for entry in entries:
                icon = "📁" if entry.is_dir() else ("🟦" if entry.suffix.lower() == ".exe" else "📄")
                size = "-" if entry.is_dir() else f"{entry.stat().st_size//1024} KB"
                mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(entry.stat().st_mtime))
                display = f"{icon} {entry.name:<32.32}   {size:>8}   {mtime}"
                if entry.is_dir() or entry.suffix.lower() == ".exe":
                    file_list.insert(tk.END, display)
        except Exception as e:
            file_list.insert(tk.END, f"Error: {e}")

    def on_select(event=None):
        sel = file_list.curselection()
        if not sel:
            return
        line = file_list.get(sel[0])
        name = line[3:].split('   ')[0].strip()
        full_path = os.path.join(current_dir.get(), name)
        if os.path.isdir(full_path):
            current_dir.set(full_path)
            update_file_list(full_path)
        elif full_path.endswith('.exe'):
            selected_file.set(full_path)
            explorer.destroy()  # Double-click on .exe selects and closes

    def on_up():
        parent = os.path.dirname(current_dir.get())
        if parent and parent != current_dir.get():
            current_dir.set(parent)
            update_file_list(parent)

    def on_confirm():
        if selected_file.get() and selected_file.get().endswith('.exe'):
            explorer.destroy()
        else:
            messagebox.showerror("Invalid Selection", "Please select a .exe file.")

    def on_cancel():
        selected_file.set("")
        explorer.destroy()

    file_list.bind('<Double-1>', on_select)
    file_list.bind('<Return>', on_select)

    # Bottom buttons
    btn_frame = tk.Frame(main_frame)
    btn_frame.pack(fill='x', pady=8)
    select_btn = tk.Button(btn_frame, text="Select", command=on_confirm)
    select_btn.pack(side='right', padx=8)
    cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel)
    cancel_btn.pack(side='right', padx=8)

    update_file_list(current_dir.get())
    explorer.transient(root)
    explorer.grab_set()
    root.wait_window(explorer)
    return selected_file.get() if selected_file.get().endswith('.exe') else None

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
    tk.Label(about, text="TuxPort", font=("Segoe UI", 20, "bold"), bg=BG, fg=ACCENT, anchor='center', justify='center').pack(pady=(24, 8), fill='x')
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

# Move download_and_run above widget creation

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
            exe_links = re.findall(r'href=["\']([^"\']+\.exe)["\']', html, re.IGNORECASE)
            if not exe_links:
                if root.winfo_exists():
                    messagebox.showerror("No .exe Found", "No .exe download links found on the page.")
                return
            exe_links = [urljoin(url, link) for link in exe_links]
            exe_url = exe_links[0]  # Just pick the first for simplicity
        temp_dir = tempfile.gettempdir()
        local_filename = os.path.join(temp_dir, os.path.basename(exe_url))
        file_label.config(text="Downloading... Please wait.")
        progress['value'] = 0
        progress.pack()  # Show progress bar
        root.update()
        req = urllib.request.Request(exe_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        })
        with urllib.request.urlopen(req) as response, open(local_filename, 'wb') as out_file:
            total_length = response.length or response.getheader('content-length')
            if total_length is None:
                out_file.write(response.read())
            else:
                total_length = int(total_length)
                downloaded = 0
                chunk_size = 8192
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded / total_length * 100)
                    progress['value'] = percent
                    root.update_idletasks()
        progress.pack_forget()  # Hide progress bar
        file_label.config(text="Download complete. Running installer...")
        root.update()
        subprocess.run(["wine", local_filename], check=True)
        file_label.config(text="Select and run a Windows installer (.exe) using Wine.")
    except Exception as e:
        progress.pack_forget()
        if root.winfo_exists():
            messagebox.showerror("Error", f"Failed to download or run installer.\n{e}")
        if root.winfo_exists():
            file_label.config(text="Select and run a Windows installer (.exe) using Wine.")

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
if dnd_available:
    root = TkinterDnD.Tk()
else:
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

progress = ttk.Progressbar(file_frame, orient='horizontal', mode='determinate', length=400, maximum=100)
progress.pack(pady=(4, 8))
progress.pack_forget()  # Hide by default

def select_exe():
    exe = filedialog.askopenfilename(
        title="Select a Windows Installer (.exe)",
        filetypes=[("Windows Executable", "*.exe")],
        initialdir=os.path.expanduser("~")
    )
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
download_btn = ttk.Button(container, text="⬇️  Download and Run .exe", command=download_and_run, style='TButton')
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

# Add drag-and-drop support for .exe files
def on_drop(event):
    file_path = event.data.strip('{}')  # Remove curly braces if present
    if file_path.lower().endswith('.exe'):
        try:
            subprocess.run(["wine", file_path], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run dropped file with Wine.\n{e}")
    else:
        messagebox.showerror("Invalid File", "Please drop a .exe file.")

if dnd_available:
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', on_drop)

root.mainloop()
