"""
控制面板 — 可视化管理鼠标拖尾样式
使用 Canvas+Scrollbar 支持小屏幕滚动
"""
import tkinter as tk
from tkinter import ttk, colorchooser
import config


class ControlPanel:
    """拖尾样式管理 GUI"""

    def __init__(self, root, engine, overlay):
        self.root = root
        self.engine = engine
        self.overlay = overlay
        self.user_config = config.load_config()

        # 主窗口
        self.window = tk.Toplevel(root)
        self.window.title("✨ 鼠标拖尾 - 控制面板")
        self.window.minsize(420, 400)
        self.window.configure(bg="#1e1e2e")
        self.window.attributes("-topmost", True)

        # 主题
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._setup_theme()

        # === 滚动区域 ===
        self.canvas = tk.Canvas(self.window, bg="#1e1e2e",
                                highlightthickness=0, width=440)
        self.scrollbar = ttk.Scrollbar(self.window, orient="vertical",
                                       command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#1e1e2e")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"))
        )
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        # Canvas 宽度随窗口变化
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # === 构建 UI（放入 scroll_frame） ===
        self._build_ui()

        # 应用当前配置
        self._apply_current_config()

        # 定位
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        w, h = 460, min(720, sh - 60)
        x = sw - w - 40
        y = (sh - h) // 2
        self.window.geometry(f"{w}x{h}+{x}+{y}")

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_theme(self):
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#cba6f7"
        dark = "#181825"

        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg,
                             font=("Microsoft YaHei", 10))
        self.style.configure("TLabelframe", background=bg, foreground=accent,
                             font=("Microsoft YaHei", 11, "bold"))
        self.style.configure("TLabelframe.Label", background=bg, foreground=accent,
                             font=("Microsoft YaHei", 11, "bold"))
        self.style.configure("TButton", background=dark, foreground=fg,
                             font=("Microsoft YaHei", 10), borderwidth=0,
                             padding=(12, 6))
        self.style.map("TButton", background=[("active", "#313244")])
        self.style.configure("TCombobox", fieldbackground=dark, background=dark,
                             foreground=fg, font=("Microsoft YaHei", 10))
        self.style.configure("TScale", background=bg, troughcolor=dark)
        self.style.configure("TRadiobutton", background=bg, foreground=fg,
                             font=("Microsoft YaHei", 9))

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_resize(self, event):
        """Canvas 宽度变化时同步内部 frame 宽度"""
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    # ==================== UI 构建 ====================

    def _build_ui(self):
        """所有控件放入 scroll_frame"""
        parent = self.scroll_frame
        pad = {"padx": 14, "pady": 5}
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#cba6f7"
        dark = "#313244"

        # === 标题 ===
        title_frame = tk.Frame(parent, bg=bg)
        title_frame.pack(fill="x", pady=(14, 6))

        tk.Label(title_frame, text="✨ 鼠标拖尾美化",
                 font=("Microsoft YaHei", 18, "bold"),
                 fg=accent, bg=bg).pack()
        tk.Label(title_frame, text="粒子 / 线条 / 混合拖尾",
                 font=("Microsoft YaHei", 9), fg="#6c7086", bg=bg).pack()

        # === 开关 ===
        switch_frame = tk.Frame(parent, bg=bg)
        switch_frame.pack(fill="x", **pad)

        self.enabled_var = tk.BooleanVar(value=True)
        self.switch_btn = tk.Button(
            switch_frame,
            text="●  拖尾已开启",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#a6e3a1", fg="#1e1e2e",
            activebackground="#94e2a0", activeforeground="#1e1e2e",
            relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
            command=self._toggle_enabled
        )
        self.switch_btn.pack(fill="x")

        # === 拖尾模式（新增） ===
        mode_frame = ttk.Labelframe(parent, text="🎯 拖尾模式", padding=10)
        mode_frame.pack(fill="x", **pad)

        self.trail_mode_var = tk.StringVar(value="particle")
        mode_row = tk.Frame(mode_frame, bg=bg)
        mode_row.pack(fill="x")
        for text, val in [("● 粒子", "particle"),
                          ("— 线条", "line"),
                          ("✦ 混合", "both")]:
            tk.Radiobutton(
                mode_row, text=text, variable=self.trail_mode_var, value=val,
                bg=bg, fg=fg, selectcolor=dark,
                activebackground=bg, activeforeground=accent,
                font=("Microsoft YaHei", 10),
                command=self._on_mode_change
            ).pack(side="left", padx=(0, 12))

        # 线宽（线条 / 混合模式时生效）
        linew_frame = tk.Frame(mode_frame, bg=bg)
        linew_frame.pack(fill="x", pady=(6, 0))
        tk.Label(linew_frame, text="线条宽度", fg=fg, bg=bg,
                 font=("Microsoft YaHei", 10)).pack(side="left")
        self.line_width_var = tk.IntVar(value=3)
        self._make_scale(linew_frame, self.line_width_var, 1, 10).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

        # 线条样式（仅线条 / 混合模式生效）
        linestyle_frame = tk.Frame(mode_frame, bg=bg)
        linestyle_frame.pack(fill="x", pady=(6, 0))
        tk.Label(linestyle_frame, text="线条样式", fg=fg, bg=bg,
                 font=("Microsoft YaHei", 10)).pack(side="left")
        self.line_style_var = tk.StringVar(value="uniform")
        for text, val in [("━ 统一", "uniform"), ("～ 尾拖", "taper")]:
            tk.Radiobutton(
                linestyle_frame, text=text, variable=self.line_style_var, value=val,
                bg=bg, fg=fg, selectcolor=dark,
                activebackground=bg, activeforeground=accent,
                font=("Microsoft YaHei", 9),
                command=self._on_line_style_change
            ).pack(side="left", padx=(0, 12))

        # === 样式预设 ===
        preset_frame = ttk.Labelframe(parent, text="🎨 样式预设", padding=10)
        preset_frame.pack(fill="x", **pad)

        preset_names = list(config.PRESETS.keys())
        self.preset_var = tk.StringVar(
            value=self.user_config.get("active_preset", "彩虹"))
        self.preset_combo = ttk.Combobox(
            preset_frame, textvariable=self.preset_var,
            values=preset_names, state="readonly", height=8,
            font=("Microsoft YaHei", 11)
        )
        self.preset_combo.pack(fill="x")
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # 预览色块
        self.preview_canvas = tk.Canvas(
            preset_frame, height=28, bg="#181825", highlightthickness=0)
        self.preview_canvas.pack(fill="x", pady=(8, 0))
        self._update_preview()

        # === 参数调节 ===
        param_frame = ttk.Labelframe(parent, text="⚙️ 参数调节", padding=10)
        param_frame.pack(fill="x", **pad)

        # 拖尾长度
        tk.Label(param_frame, text="拖尾长度（影响粒子密度）",
                 fg=fg, bg=bg, font=("Microsoft YaHei", 10)).pack(anchor="w")
        self.length_var = tk.IntVar(value=20)
        self._make_scale(param_frame, self.length_var, 5, 80).pack(fill="x")

        # 粒子大小
        tk.Label(param_frame, text="粒子大小", fg=fg, bg=bg,
                 font=("Microsoft YaHei", 10)).pack(anchor="w", pady=(8, 0))
        self.size_var = tk.IntVar(value=6)
        self._make_scale(param_frame, self.size_var, 2, 18).pack(fill="x")

        # 衰减速度
        tk.Label(param_frame, text="衰减速度（越大越快消失）",
                 fg=fg, bg=bg, font=("Microsoft YaHei", 10)).pack(
            anchor="w", pady=(8, 0))
        self.fade_var = tk.DoubleVar(value=0.06)
        self._make_scale(param_frame, self.fade_var, 0.01, 0.2,
                         resolution=0.01).pack(fill="x")

        # 粒子形状
        shape_frame = tk.Frame(param_frame, bg=bg)
        shape_frame.pack(fill="x", pady=(10, 0))
        tk.Label(shape_frame, text="粒子形状", fg=fg, bg=bg,
                 font=("Microsoft YaHei", 10)).pack(side="left")
        self.shape_var = tk.StringVar(value="circle")
        for text, val in [("● 圆形", "circle"), ("■ 方形", "square"),
                          ("★ 星形", "star")]:
            tk.Radiobutton(
                shape_frame, text=text, variable=self.shape_var, value=val,
                bg=bg, fg=fg, selectcolor=dark,
                activebackground=bg, activeforeground=accent,
                font=("Microsoft YaHei", 9),
                command=self._on_shape_change
            ).pack(side="left", padx=(0, 10))

        # === 自定义颜色 ===
        color_frame = ttk.Labelframe(parent, text="🎯 自定义颜色", padding=10)
        color_frame.pack(fill="x", **pad)

        color_row = tk.Frame(color_frame, bg=bg)
        color_row.pack(fill="x")

        self.color_btn = tk.Button(
            color_row, text="选择颜色", font=("Microsoft YaHei", 10),
            bg=dark, fg=fg, relief="flat",
            padx=12, pady=4, cursor="hand2",
            command=self._pick_color
        )
        self.color_btn.pack(side="left", padx=(0, 10))

        self.color_label = tk.Label(
            color_row, text="  ", font=("Microsoft YaHei", 8),
            bg=self.user_config.get("custom_color", "#ff00ff"),
            width=4, height=1
        )
        self.color_label.pack(side="left")

        self.color_mode_var = tk.StringVar(value="solid")
        for text, val in [("纯色", "solid"), ("彩虹", "rainbow")]:
            tk.Radiobutton(
                color_row, text=text, variable=self.color_mode_var, value=val,
                bg=bg, fg=fg, selectcolor=dark,
                activebackground=bg, activeforeground=accent,
                font=("Microsoft YaHei", 9), command=self._apply_custom
            ).pack(side="left", padx=(12, 0) if text == "纯色" else (6, 0))

        tk.Button(
            color_row, text="应用", font=("Microsoft YaHei", 10, "bold"),
            bg=accent, fg=bg, relief="flat",
            padx=14, pady=4, cursor="hand2",
            command=self._apply_custom
        ).pack(side="right")


        # === 光标装饰 ===
        cursor_frame = ttk.Labelframe(parent, text="🖱 光标装饰", padding=10)
        cursor_frame.pack(fill="x", **pad)

        # 开关
        cursor_btn_frame = tk.Frame(cursor_frame, bg=bg)
        cursor_btn_frame.pack(fill="x", pady=(0, 6))

        self.cursor_btn = tk.Button(
            cursor_btn_frame,
            text="● 光标装饰已开启",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#a6e3a1", fg="#1e1e2e",
            activebackground="#94e2a0", activeforeground="#1e1e2e",
            relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
            command=self._toggle_cursor
        )
        self.cursor_btn.pack(fill="x")

        # 图片选择
        image_row = tk.Frame(cursor_frame, bg=bg)
        image_row.pack(fill="x", pady=(4, 0))
        tk.Button(
            image_row, text="选择图片...", font=("Microsoft YaHei", 10),
            bg=dark, fg=fg, relief="flat",
            padx=12, pady=4, cursor="hand2",
            command=self._select_cursor_image
        ).pack(side="left", padx=(0, 8))
        self.cursor_path_label = tk.Label(
            image_row, text="(未选择)", fg="#6c7086", bg=bg,
            font=("Microsoft YaHei", 9), wraplength=200,
            anchor="w", justify="left"
        )
        self.cursor_path_label.pack(side="left", fill="x", expand=True)
        tk.Button(
            image_row, text="清除", font=("Microsoft YaHei", 9),
            bg="#6c7086", fg=bg, relief="flat",
            padx=8, pady=2, cursor="hand2",
            command=self._clear_cursor_image
        ).pack(side="right")

        # 大小
        size_row = tk.Frame(cursor_frame, bg=bg)
        size_row.pack(fill="x", pady=(4, 0))
        tk.Label(size_row, text="大小", fg=fg, bg=bg,
                 font=("Microsoft YaHei", 10)).pack(side="left")
        self.cursor_size_var = tk.IntVar(value=12)
        tk.Scale(
            size_row, orient="horizontal", variable=self.cursor_size_var,
            from_=4, to=40, bg=bg, fg=fg, highlightthickness=0,
            troughcolor=dark, activebackground=accent,
            command=self._on_cursor_size_change
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

        # === 底部按钮 ===
        bottom_frame = tk.Frame(parent, bg=bg)
        bottom_frame.pack(fill="x", side="bottom", **pad)

        tk.Button(
            bottom_frame, text="🧹 清除拖尾", font=("Microsoft YaHei", 10),
            bg=dark, fg=fg, relief="flat",
            padx=14, pady=6, cursor="hand2",
            command=self._clear_trail
        ).pack(fill="x", pady=(0, 4))

        tk.Button(
            bottom_frame, text="❌ 退出程序", font=("Microsoft YaHei", 10),
            bg="#f38ba8", fg=bg, relief="flat",
            padx=14, pady=6, cursor="hand2",
            command=self._on_close
        ).pack(fill="x")

    def _make_scale(self, parent, variable, from_val, to_val, resolution=None):
        kw = {
            "orient": "horizontal", "variable": variable,
            "from_": from_val, "to": to_val,
            "bg": "#1e1e2e", "fg": "#cdd6f4",
            "highlightthickness": 0, "troughcolor": "#313244",
            "activebackground": "#cba6f7",
            "command": self._on_param_change,
        }
        if resolution is not None:
            kw["resolution"] = resolution
        return tk.Scale(parent, **kw)

    # ==================== 事件处理 ====================

    def _on_preset_change(self, event=None):
        name = self.preset_var.get()
        preset = config.get_preset(name)
        self._apply_preset_to_ui(preset)
        self._apply_to_engine(preset)
        self._update_preview()
        self._save_config()

    def _on_param_change(self, event=None):
        self._apply_to_engine_from_ui()
        self._update_preview()
        self._save_config()

    def _on_shape_change(self):
        self._apply_to_engine_from_ui()
        self._save_config()

    def _on_mode_change(self):
        self._apply_to_engine_from_ui()
        self._save_config()

    def _on_line_style_change(self):
        self._apply_to_engine_from_ui()
        self._save_config()

    def _toggle_enabled(self):
        self.engine.enabled = not self.engine.enabled
        if self.engine.enabled:
            self.switch_btn.config(text="●  拖尾已开启", bg="#a6e3a1")
        else:
            self.switch_btn.config(text="○  拖尾已关闭", bg="#f38ba8")
            self.engine.clear()
        self._save_config()
    # ==================== 光标装饰控制 ====================

    def _toggle_cursor(self):
        self.engine.cursor_enabled = not self.engine.cursor_enabled
        if self.engine.cursor_enabled:
            self.cursor_btn.config(text="● 光标装饰已开启", bg="#a6e3a1")
        else:
            self.cursor_btn.config(text="○ 光标装饰已关闭", bg="#f38ba8")
        self._save_config()

    def _select_cursor_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="选择光标图像",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp *.ico *.cur"),
                ("所有文件", "*.*"),
            ]
        )
        if not path:
            return
        self.user_config["cursor_image_path"] = path
        self.engine.select_cursor_image(path)
        self.cursor_path_label.config(text=path, fg="#cdd6f4")
        # 如果光标装饰未启用则自动开启
        if not self.engine.cursor_enabled:
            self._toggle_cursor()
        self._save_config()

    def _clear_cursor_image(self):
        self.user_config["cursor_image_path"] = ""
        self.engine.clear_cursor_image()
        self.cursor_path_label.config(text="(未选择)", fg="#6c7086")
        self._save_config()

    def _on_cursor_size_change(self, event=None):
        self.engine.cursor_size = self.cursor_size_var.get()
        self._save_config()

    def _apply_cursor_to_engine(self):
        self.engine.cursor_enabled = self.user_config.get("cursor_enabled", True)
        self.engine.cursor_size = self.user_config.get("cursor_size", 32)
        # 加载光标图像
        img_path = self.user_config.get("cursor_image_path", "")
        self.engine.select_cursor_image(img_path)


    def _pick_color(self):
        result = colorchooser.askcolor(
            initialcolor=self.user_config.get("custom_color", "#ff00ff"),
            title="选择拖尾颜色"
        )
        if result[1]:
            self.user_config["custom_color"] = result[1]
            self.color_label.config(bg=result[1])
            self._apply_custom()

    def _apply_custom(self):
        hex_color = self.user_config.get("custom_color", "#ff00ff")
        mode = self.color_mode_var.get()
        preset = {
            "name": "自定义",
            "color_mode": mode,
            "colors": [hex_color],
            "particle_size": self.size_var.get(),
            "trail_length": self.length_var.get(),
            "fade_speed": self.fade_var.get(),
            "line_width": self.line_width_var.get(),
            "shape": self.shape_var.get(),
            "trail_mode": self.trail_mode_var.get(),
            "line_style": self.line_style_var.get(),
        }
        self._apply_to_engine(preset)
        self._update_preview()
        self._save_config()

    def _clear_trail(self):
        self.engine.clear()

    def _on_close(self):
        self.engine.clear()
        self._save_config()
        self.overlay.stop()
        try:
            self.window.destroy()
        except Exception:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    # ==================== 应用配置 ====================

    def _apply_preset_to_ui(self, preset):
        self.length_var.set(preset["trail_length"])
        self.size_var.set(preset["particle_size"])
        self.fade_var.set(preset["fade_speed"])
        self.shape_var.set(preset.get("shape", "circle"))
        self.trail_mode_var.set(preset.get("trail_mode", "particle"))
        self.line_width_var.set(preset.get("line_width", 3))
        self.line_style_var.set(preset.get("line_style", "uniform"))

    def _apply_to_engine(self, preset):
        self.engine.set_config(preset)
        self.engine.cursor_enabled = self.user_config.get("cursor_enabled", True)
        self.engine.cursor_size = self.user_config.get("cursor_size", 32)
        self.engine.select_cursor_image(self.user_config.get("cursor_image_path", ""))

    def _apply_to_engine_from_ui(self):
        preset = {
            "name": "自定义",
            "color_mode": self.engine.color_mode,
            "colors": self.engine.colors_hex,
            "particle_size": self.size_var.get(),
            "trail_length": self.length_var.get(),
            "fade_speed": self.fade_var.get(),
            "line_width": self.line_width_var.get(),
            "shape": self.shape_var.get(),
            "trail_mode": self.trail_mode_var.get(),
            "line_style": self.line_style_var.get(),
        }
        self._apply_to_engine(preset)

    def _update_preview(self):
        self.preview_canvas.delete("all")
        preset_name = self.preset_var.get()
        preset = config.get_preset(preset_name)
        colors = preset["colors"]
        w = self.preview_canvas.winfo_width()
        if w < 10:
            w = 400
        h = 28
        n = len(colors)
        if n == 0:
            return
        seg_w = w / n
        for i, c in enumerate(colors):
            x1 = i * seg_w
            x2 = (i + 1) * seg_w
            self.preview_canvas.create_rectangle(x1, 0, x2, h, fill=c, outline="")

    def _apply_current_config(self):
        name = self.user_config.get("active_preset", "彩虹")
        self.preset_var.set(name)
        preset = config.get_preset(name)
        self._apply_preset_to_ui(preset)
        self._apply_to_engine(preset)

        self.engine.enabled = self.user_config.get("enabled", True)
        self.enabled_var.set(self.engine.enabled)
        if not self.engine.enabled:
            self.switch_btn.config(text="○  拖尾已关闭", bg="#f38ba8")

        self.color_label.config(bg=self.user_config.get("custom_color", "#ff00ff"))
        self._update_preview()

        # 初始化光标装饰状态
        self.cursor_size_var.set(self.user_config.get("cursor_size", 32))
        self._apply_cursor_to_engine()
        img_path = self.user_config.get("cursor_image_path", "")
        if img_path:
            self.cursor_path_label.config(text=img_path, fg="#cdd6f4")
        if not self.engine.cursor_enabled:
            self.cursor_btn.config(text="○ 光标装饰已关闭", bg="#f38ba8")

    def _save_config(self):
        self.user_config["active_preset"] = self.preset_var.get()
        self.user_config["enabled"] = self.engine.enabled
        self.user_config["cursor_enabled"] = self.engine.cursor_enabled
        self.user_config["cursor_size"] = self.engine.cursor_size
        self.user_config["cursor_image_path"] = self.engine.cursor_image_path
        config.save_config(self.user_config)




