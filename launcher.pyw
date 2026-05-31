# SPDX-License-Identifier: AGPL-3.0
"""
终末地伤害计算器 — 图形化启动器

双击此文件打开启动窗口，点「启动服务器」即可在浏览器中使用。
"""
from __future__ import annotations

import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

_REPO = Path(__file__).resolve().parent


try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    # 极少数 Windows 精简安装可能没有 tkinter
    import ctypes
    ctypes.windll.user32.MessageBoxW(0,
        "启动失败：当前 Python 环境缺少 tkinter 模块。\n\n"
        "请使用标准 Python 安装，或双击「启动本地服务器.bat」运行。",
        "终末地伤害计算器", 0)
    sys.exit(1)


class Launcher:
    """简单的服务器启动器窗口。"""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("终末地伤害计算器")
        self.root.geometry("480x280")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        # 居中
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 480) // 2
        y = (self.root.winfo_screenheight() - 280) // 2
        self.root.geometry(f"+{x}+{y}")

        self._process: subprocess.Popen | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        fg = "#333"

        # 标题
        tk.Label(self.root, text="终末地伤害计算器",
                 font=("Microsoft YaHei", 18, "bold"),
                 fg="#1a73e8", bg="#f5f5f5").pack(pady=(24, 4))
        tk.Label(self.root, text="本地服务器启动器",
                 font=("Microsoft YaHei", 10),
                 fg=fg, bg="#f5f5f5").pack()

        # 状态
        self._status_var = tk.StringVar(value="就绪")
        self._status_label = tk.Label(
            self.root, textvariable=self._status_var,
            font=("Microsoft YaHei", 10), fg="#666", bg="#f5f5f5",
        )
        self._status_label.pack(pady=(12, 4))

        # 按钮
        btn_frame = tk.Frame(self.root, bg="#f5f5f5")
        btn_frame.pack(pady=12)

        self._start_btn = tk.Button(
            btn_frame, text="启动服务器",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#1a73e8", fg="white", width=18, height=1,
            bd=0, padx=16, pady=6, cursor="hand2",
            activebackground="#1557b0", activeforeground="white",
            command=self._start_server,
        )
        self._start_btn.pack()

        self._open_btn = tk.Button(
            btn_frame, text="打开浏览器",
            font=("Microsoft YaHei", 10),
            bg="#e8e8e8", fg=fg, width=18, height=1,
            bd=0, padx=16, pady=4, cursor="hand2",
            state="disabled",
            command=lambda: webbrowser.open("http://localhost:8180"),
        )
        self._open_btn.pack(pady=(6, 0))

        self._stop_btn = tk.Button(
            btn_frame, text="停止服务器",
            font=("Microsoft YaHei", 10),
            bg="#e8e8e8", fg=fg, width=18, height=1,
            bd=0, padx=16, pady=4, cursor="hand2",
            state="disabled",
            command=self._stop_server,
        )
        self._stop_btn.pack()

        # 提示
        tk.Label(self.root,
                 text="启动后会在浏览器中打开本地页面\n"
                      "全量搜索使用你的电脑 GPU 计算，速度与桌面版一致",
                 font=("Microsoft YaHei", 9), fg="#999", bg="#f5f5f5",
                 justify="center").pack(pady=(8, 0))

    def _set_status(self, text: str, color: str = "#666") -> None:
        self._status_var.set(text)
        self._status_label.configure(fg=color)
        self.root.update()

    def _start_server(self) -> None:
        self._start_btn.configure(state="disabled", text="启动中...")
        self._set_status("正在启动...", "#1a73e8")

        def _run() -> None:
            try:
                self._process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "main:app",
                     "--host", "127.0.0.1", "--port", "8180"],
                    cwd=str(_REPO / "web" / "backend"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True, encoding="utf-8", errors="replace",
                )
                # 等待服务器就绪
                import time
                time.sleep(2)

                self.root.after(0, self._on_server_ready)
            except Exception as e:
                self.root.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_server_ready(self) -> None:
        self._set_status("服务器已启动 → http://localhost:8180", "#2e7d32")
        self._start_btn.configure(text="启动服务器")
        self._open_btn.configure(state="normal")
        self._stop_btn.configure(state="normal")
        webbrowser.open("http://localhost:8180")

    def _on_error(self, msg: str) -> None:
        self._set_status(f"启动失败: {msg}", "#d32f2f")
        self._start_btn.configure(state="normal", text="启动服务器")
        messagebox.showerror("启动失败", msg)

    def _stop_server(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None
        self._set_status("已停止", "#666")
        self._start_btn.configure(state="normal")
        self._open_btn.configure(state="disabled")
        self._stop_btn.configure(state="disabled")

    def run(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self) -> None:
        self._stop_server()
        self.root.destroy()


if __name__ == "__main__":
    Launcher().run()
