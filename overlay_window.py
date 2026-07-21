"""
透明覆盖窗口 — 在所有窗口之上渲染鼠标拖尾效果
使用 Toplevel 共享主 root 的 mainloop
"""
import tkinter as tk
import queue
import ctypes


class OverlayWindow:
    """全屏透明覆盖层，用于渲染鼠标拖尾粒子"""

    def __init__(self, root, engine):
        self.engine = engine
        self.running = False
        self.mouse_x = 0
        self.mouse_y = 0
        self._pos_queue = queue.Queue(maxsize=64)
        self._after_id = None
        self._cursor_was_hidden = False

        # 获取屏幕尺寸
        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()

        # 创建透明 Toplevel 窗口
        self.window = tk.Toplevel(root)
        self.window.title("Mouse Trail Overlay")
        self.window.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        # 透明 + 置顶 + 无边框
        self.window.attributes("-topmost", True)
        self.window.attributes("-transparentcolor", "#000001")
        self.window.overrideredirect(True)
        self.window.configure(bg="#000001")

        # 画布
        self.canvas = tk.Canvas(
            self.window,
            width=self.screen_w,
            height=self.screen_h,
            bg="#000001",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # 延迟设置点击穿透（等窗口完全创建后）
        self.window.after(200, self._make_click_through)

        # 绑定关闭
        self.window.protocol("WM_DELETE_WINDOW", self.stop)

    def _make_click_through(self):
        """设置窗口点击穿透 (Windows API)"""
        try:
            user32 = ctypes.windll.user32

            # 获取 Toplevel 窗口的实际 HWND
            hwnd = self.window.winfo_id()

            # 确保是实际的顶层窗口句柄
            # GA_ROOT = 2
            hwnd_root = user32.GetAncestor(hwnd, 2)
            if hwnd_root and hwnd_root != hwnd:
                hwnd = hwnd_root

            # GWL_EXSTYLE = -20
            # WS_EX_LAYERED = 0x80000
            # WS_EX_TRANSPARENT = 0x20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20

            ex_style = user32.GetWindowLongW(hwnd, -20)
            ex_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, -20, ex_style)

            # 刷新窗口
            # SWP_NOMOVE=0x2, SWP_NOSIZE=0x1, SWP_NOZORDER=0x4, SWP_FRAMECHANGED=0x20
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                               0x2 | 0x1 | 0x4 | 0x20)
        except Exception:
            pass  # 非 Windows 环境忽略

    def enqueue_position(self, x, y):
        """将鼠标位置放入队列（线程安全）"""
        try:
            self._pos_queue.put_nowait((x, y))
        except queue.Full:
            # 队列满时丢弃最旧的位置，放入新位置
            try:
                self._pos_queue.get_nowait()
                self._pos_queue.put_nowait((x, y))
            except queue.Empty:
                pass

    def _drain_queue(self):
        """
        在主线程中一次性取出队列中的所有位置。
        返回位置列表（按时间顺序），不丢失任何中间位置，
        确保 Catmull-Rom 样条能够拟合出真实的鼠标移动曲线。
        """
        positions = []
        try:
            while True:
                x, y = self._pos_queue.get_nowait()
                positions.append((x, y))
        except queue.Empty:
            pass
        return positions

    def _render_loop(self):
        """渲染循环 (约 60 FPS)"""
        if not self.running:
            return

        # 取出本帧内所有鼠标位置
        positions = self._drain_queue()

        # 更新最后已知位置（用于初始帧）
        if positions:
            self.mouse_x, self.mouse_y = positions[-1]

        # 更新引擎 — 传入所有位置以便样条插值
        if self.engine.enabled:
            self.engine.feed_and_update(positions)

        # 清除画布并重绘
        self.canvas.delete("all")
        self.engine.draw(self.canvas)

        # 光标装饰：隐藏系统鼠标 + 绘制自定义光标图像
        cursor_active = self.engine.cursor_enabled and bool(self.engine.cursor_image_path)
        if cursor_active:
            if not self._cursor_was_hidden:
                self.engine.hide_system_cursor()
                self._cursor_was_hidden = True
            self.engine.draw_cursor(self.canvas, self.mouse_x, self.mouse_y)
        else:
            if self._cursor_was_hidden:
                self.engine.show_system_cursor()
                self._cursor_was_hidden = False

        # 限制最大粒子数 / 线条点数（性能保护）
        cap = self.engine.max_particles
        if len(self.engine.particles) > cap:
            self.engine.particles = self.engine.particles[-cap:]

        # 下一帧
        self._after_id = self.window.after(16, self._render_loop)

    def start(self):
        """开始渲染循环"""
        self.running = True
        self.window.after(50, self._render_loop)

    def stop(self):
        """停止覆盖窗口"""
        self.running = False
        # 恢复系统鼠标
        if self._cursor_was_hidden:
            self.engine.show_system_cursor()
            self._cursor_was_hidden = False
        if self._after_id:
            self.window.after_cancel(self._after_id)
        try:
            self.window.destroy()
        except Exception:
            pass

