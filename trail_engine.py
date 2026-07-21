"""
粒子引擎 — 管理拖尾粒子的生命周期、物理和渲染
支持粒子模式 / 线条模式 / 混合模式，Catmull-Rom 样条平滑。
"""
import math
import random
import collections
import colorsys


class Particle:
    """单个拖尾粒子"""
    __slots__ = ("x", "y", "size", "color", "alpha", "vx", "vy", "life", "max_life")

    def __init__(self, x, y, size, color, life=1.0):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.alpha = 1.0
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.2, 0.8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = life
        self.max_life = life


class TrailEngine:
    """拖尾效果引擎 — 粒子 + 线条双模式"""

    def __init__(self):
        self.particles = []
        self._pos_history = collections.deque(maxlen=120)
        self._cursor = 0
        self._hue_offset = 0.0
        self._spacing = 5

        # 线条拖尾缓冲区
        self._line_buffer = collections.deque(maxlen=300)

        # 默认配置
        self.color_mode = "rainbow"
        self.colors_hex = ["#ff0000", "#ff8800", "#ffff00"]
        self.colors_rgb = [(255, 0, 0), (255, 136, 0), (255, 255, 0)]
        self.particle_size = 6
        self.trail_length = 20
        self.fade_speed = 0.06
        self.line_width = 3
        self.shape = "circle"
        self.enabled = True
        self.trail_mode = "particle"  # particle | line | both
        self.line_style = "uniform"   # uniform | taper
        self._max_particles = 2000

        # 光标装饰设置
        self.cursor_enabled = True
        self.cursor_size = 32
        self.cursor_image_path = ""         # 文件路径，空 = 不使用

        self._cursor_tk_image = None          # tkinter.PhotoImage 缓存

    def set_config(self, preset):
        """应用预设配置"""
        self.color_mode = preset["color_mode"]
        self.colors_hex = preset["colors"]
        self.colors_rgb = [self._hex_to_rgb(c) for c in preset["colors"]]
        self.particle_size = preset["particle_size"]
        self.trail_length = preset["trail_length"]
        self.fade_speed = preset["fade_speed"]
        self.line_width = preset.get("line_width", 3)
        self.shape = preset.get("shape", "circle")
        self.trail_mode = preset.get("trail_mode", "particle")
        self.line_style = preset.get("line_style", "uniform")  # uniform | taper
        self._spacing = max(2, self.particle_size // 2)
        # 拖尾长度 → 最大粒子数：trail_length × 100
        self._max_particles = max(300, self.trail_length * 100)

    @staticmethod
    def _hex_to_rgb(hex_color):
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    # ==================== Catmull-Rom 样条 ====================

    @staticmethod
    def _catmull_rom(p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        x = 0.5 * (
            (2.0 * p1[0])
            + (-p0[0] + p2[0]) * t
            + (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2
            + (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
        )
        y = 0.5 * (
            (2.0 * p1[1])
            + (-p0[1] + p2[1]) * t
            + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
            + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
        )
        return (x, y)

    @staticmethod
    def _mirror_point(pt, neighbor):
        return (2.0 * pt[0] - neighbor[0], 2.0 * pt[1] - neighbor[1])

    def _get_control_points(self, hist, seg_idx):
        p1 = hist[seg_idx]
        p2 = hist[seg_idx + 1]
        p0 = hist[seg_idx - 1] if seg_idx > 0 else self._mirror_point(p1, p2)
        p3 = hist[seg_idx + 2] if seg_idx + 2 < len(hist) else self._mirror_point(p2, p1)
        return p0, p1, p2, p3

    # ==================== 主更新 ====================

    def feed_and_update(self, positions):
        """
        每帧调用：生成粒子 / 线条点，更新生命周期。
        """
        # --- 1. 追加位置到历史 ---
        if positions:
            for x, y in positions:
                self._pos_history.append((x, y))

        hist = list(self._pos_history)
        n = len(hist)

        # --- 2. 沿 Catmull-Rom 路径生成粒子 ---
        has_new = n >= 2 and self._cursor < n - 1
        if has_new and self.trail_mode in ("particle", "both"):
            unprocessed = hist[self._cursor:]
            seg_count = len(unprocessed) - 1
            seg_dists = []
            total_dist = 0.0
            for s in range(seg_count):
                d = math.hypot(unprocessed[s + 1][0] - unprocessed[s][0],
                               unprocessed[s + 1][1] - unprocessed[s][1])
                seg_dists.append(d)
                total_dist += d

            if total_dist >= self._spacing:
                steps = max(1, int(total_dist / self._spacing))
                accumulated = 0.0
                seg_idx = 0
                for j in range(steps):
                    target = (j + 1) / (steps + 1) * total_dist
                    while seg_idx < seg_count and accumulated + seg_dists[seg_idx] < target:
                        accumulated += seg_dists[seg_idx]
                        seg_idx += 1
                    if seg_idx >= seg_count:
                        seg_idx = seg_count - 1

                    seg_d = seg_dists[seg_idx] if seg_dists[seg_idx] > 0 else 1.0
                    local_t = (target - accumulated) / seg_d
                    local_t = max(0.0, min(1.0, local_t))

                    global_si = self._cursor + seg_idx
                    p0, p1, p2, p3 = self._get_control_points(hist, global_si)
                    px, py = self._catmull_rom(p0, p1, p2, p3, local_t)
                    self.particles.append(
                        Particle(px, py, self.particle_size, self._get_color(), life=1.0)
                    )

        # --- 3. 线条拖尾采样（使用同一个 cursor，不依赖粒子是否执行） ---
        if has_new and self.trail_mode in ("line", "both"):
            line_spacing = self._spacing * 2
            unprocessed = hist[self._cursor:]
            seg_count = len(unprocessed) - 1
            seg_dists = []
            total_dist = 0.0
            for s in range(seg_count):
                d = math.hypot(unprocessed[s + 1][0] - unprocessed[s][0],
                               unprocessed[s + 1][1] - unprocessed[s][1])
                seg_dists.append(d)
                total_dist += d

            if total_dist >= line_spacing:
                steps = max(1, int(total_dist / line_spacing))
                accumulated = 0.0
                seg_idx = 0
                for j in range(steps):
                    target = (j + 1) / (steps + 1) * total_dist
                    while seg_idx < seg_count and accumulated + seg_dists[seg_idx] < target:
                        accumulated += seg_dists[seg_idx]
                        seg_idx += 1
                    if seg_idx >= seg_count:
                        seg_idx = seg_count - 1
                    seg_d = seg_dists[seg_idx] if seg_dists[seg_idx] > 0 else 1.0
                    local_t = (target - accumulated) / seg_d
                    local_t = max(0.0, min(1.0, local_t))

                    global_si = self._cursor + seg_idx
                    p0, p1, p2, p3 = self._get_control_points(hist, global_si)
                    lx, ly = self._catmull_rom(p0, p1, p2, p3, local_t)
                    self._line_buffer.append((lx, ly, self._get_color(), 1.0))

        if has_new:
            self._cursor = n - 1

        # --- 4. 修剪历史 ---
        # 保留更多历史点，确保快速移动时 Catmull-Rom 样条有足够的控制点来拟合曲线
        while len(self._pos_history) > 60:
            self._pos_history.popleft()
            self._cursor -= 1
        self._cursor = max(0, self._cursor)

        # --- 5. 静止呼吸粒子 ---
        if self.trail_mode in ("particle", "both"):
            if self._pos_history and 0 < len(self.particles) < 3:
                mx, my = self._pos_history[-1]
                self.particles.append(
                    Particle(mx + random.uniform(-3, 3), my + random.uniform(-3, 3),
                             self.particle_size * 0.7, self._get_color(), life=0.5)
                )

        # --- 6. 更新粒子 ---
        alive = []
        for p in self.particles:
            p.life -= self.fade_speed
            if p.life <= 0:
                continue
            p.x += p.vx
            p.y += p.vy
            p.alpha = p.life
            p.size *= 0.995
            alive.append(p)
        self.particles = alive

        # --- 7. 更新线条缓冲区 ---
        kept_lines = []
        for item in self._line_buffer:
            x, y, color, life = item
            life -= self.fade_speed * 0.7  # 线条衰减比粒子慢一些
            if life > 0:
                kept_lines.append((x, y, color, life))
        self._line_buffer = collections.deque(kept_lines, maxlen=300)

        # --- 8. 彩虹色相 ---
        if self.color_mode == "rainbow":
            self._hue_offset = (self._hue_offset + 0.006) % 1.0

    def _get_color(self):
        if self.color_mode == "solid":
            return self.colors_rgb[0]
        elif self.color_mode == "gradient":
            return self.colors_rgb[random.randint(0, len(self.colors_rgb) - 1)]
        elif self.color_mode == "rainbow":
            hue = (self._hue_offset + random.uniform(-0.06, 0.06)) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            return (int(r * 255), int(g * 255), int(b * 255))
        return self.colors_rgb[0]

    def get_particles(self):
        return self.particles

    def clear(self):
        self.particles.clear()
        self._line_buffer.clear()
        self._pos_history.clear()
        self._cursor = 0

    # ==================== 渲染 ====================

    def draw(self, canvas):
        """在 Canvas 上绘制粒子 + 线条"""
        if self.trail_mode in ("particle", "both"):
            self._draw_particles(canvas)
        if self.trail_mode in ("line", "both"):
            self._draw_line_trail(canvas)

    def _draw_particles(self, canvas):
        """绘制所有粒子"""
        for p in self.particles:
            r, g, b = p.color
            sz = max(0.5, p.size * p.alpha)
            x, y = p.x, p.y

            if sz < 1.5:
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_oval(x - sz, y - sz, x + sz, y + sz,
                                   fill=color, outline="", width=0)
            elif self.shape == "square":
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_rectangle(x - sz, y - sz, x + sz, y + sz,
                                        fill=color, outline="", width=0)
            elif self.shape == "star":
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_polygon(
                    self._star_points(x, y, sz), fill=color, outline="", width=0)
            else:
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_oval(x - sz, y - sz, x + sz, y + sz,
                                   fill=color, outline="", width=0)
                glow = sz * 1.6
                canvas.create_oval(x - glow, y - glow, x + glow, y + glow,
                                   fill="", outline=color, width=1)

    def _draw_line_trail(self, canvas):
        """
        绘制线条拖尾。
        - uniform: 多层平滑曲线 + 光晕
        - taper: 中间粗两边细的尾拖效果，用分段线段模拟变宽曲线
        """
        buf = list(self._line_buffer)
        if len(buf) < 2:
            return

        if self.line_style == "taper":
            self._draw_taper_line(canvas, buf)
        else:
            self._draw_uniform_line(canvas, buf)

    def _draw_uniform_line(self, canvas, buf):
        """统一宽度线条：多层重叠模拟发光"""
        # 构建扁平坐标列表
        flat = []
        for item in buf:
            flat.extend((item[0], item[1]))

        # 取最新点的颜色作为基准
        base_color = buf[-1][2]
        r, g, b = base_color

        # 外层光晕（宽、半透明）
        outer = f"#{r//2:02x}{g//2:02x}{b//2:02x}"
        canvas.create_line(*flat, smooth=True, width=self.line_width + 4,
                           fill=outer, capstyle="round", joinstyle="round")

        # 中层
        mid = f"#{int(r*0.7):02x}{int(g*0.7):02x}{int(b*0.7):02x}"
        canvas.create_line(*flat, smooth=True, width=self.line_width + 1,
                           fill=mid, capstyle="round", joinstyle="round")

        # 核心亮线
        canvas.create_line(*flat, smooth=True, width=max(1, self.line_width - 1),
                           fill=f"#{r:02x}{g:02x}{b:02x}",
                           capstyle="round", joinstyle="round")

    def _draw_taper_line(self, canvas, buf):
        """
        尾拖效果：中间粗两边细。
        用 sin(life * pi) 控制宽度曲线，在 trail 中段达到峰值。
        由于 tkinter create_line 不支持单线变宽，
        改为逐段绘制，每段宽度 = 两端 life 均值对应的 taper 值。

        同时绘制外层光晕段 + 核心段，保持视觉层次。
        """
        import math as _math

        # 获取 buffer 中 life 的范围，用于归一化
        life_values = [item[3] for item in buf]
        min_life = min(life_values)
        max_life = max(life_values)
        life_range = max_life - min_life
        if life_range < 0.001:
            life_range = 1.0

        # 峰值位置：life=0.5（归一化后）
        peak_norm = 0.5

        for i in range(len(buf) - 1):
            x1, y1, color1, life1 = buf[i]
            x2, y2, color2, life2 = buf[i + 1]

            # 归一化 life → [0, 1]，0=尾端，1=头部（最新）
            norm1 = (life1 - min_life) / life_range
            norm2 = (life2 - min_life) / life_range

            # 用 sin 曲线：尾(0)→中(peak)→头(0)
            w1 = _math.sin(norm1 * _math.pi)
            w2 = _math.sin(norm2 * _math.pi)
            avg_taper = (w1 + w2) / 2.0

            if avg_taper < 0.03:
                continue

            seg_width = max(0.5, self.line_width * avg_taper)

            # 使用两端颜色的均值
            r = (color1[0] + color2[0]) // 2
            g = (color1[1] + color2[1]) // 2
            b = (color1[2] + color2[2]) // 2

            # 外层光晕
            glow_color = f"#{r//3:02x}{g//3:02x}{b//3:02x}"
            glow_w = seg_width + max(2, seg_width * 0.8)
            canvas.create_line(x1, y1, x2, y2,
                               width=glow_w,
                               fill=glow_color,
                               capstyle="round")

            # 核心亮线
            core_color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(x1, y1, x2, y2,
                               width=seg_width,
                               fill=core_color,
                               capstyle="round")

    # ==================== 光标装饰绘制 ====================

    def draw_cursor(self, canvas, x, y):
        """在鼠标位置绘制自定义光标图像代替系统鼠标"""
        if not self.cursor_enabled:
            return
        if not self.cursor_image_path:
            return
        if self._cursor_tk_image is None:
            if not self._load_cursor_image():
                return
        if self._cursor_tk_image is None:
            return
        canvas.create_image(x, y, image=self._cursor_tk_image, anchor="center")

    def _load_cursor_image(self):
        """从 cursor_image_path 加载并缩放到 cursor_size"""
        if not self.cursor_image_path:
            self._cursor_tk_image = None
            return False
        try:
            from PIL import Image, ImageTk
            pil_img = Image.open(self.cursor_image_path)
            sz = max(8, self.cursor_size)
            pil_img = pil_img.resize((sz, sz), Image.Resampling.LANCZOS)
            if pil_img.mode != "RGBA":
                pil_img = pil_img.convert("RGBA")
            self._cursor_tk_image = ImageTk.PhotoImage(pil_img)
            return True
        except Exception:
            self._cursor_tk_image = None
            return False

    def select_cursor_image(self, path):
        """选择新的光标图像，下次渲染时加载"""
        self.cursor_image_path = path
        self._cursor_tk_image = None

    def clear_cursor_image(self):
        """清除光标图像，恢复系统鼠标"""
        self.cursor_image_path = ""
        self._cursor_tk_image = None

    # ==================== 系统鼠标显隐 ====================

    def hide_system_cursor(self):
        """隐藏系统鼠标指针"""
        import ctypes as _ct
        try:
            user32 = _ct.windll.user32
            while user32.ShowCursor(False) >= 0:
                pass
        except Exception:
            pass

    def show_system_cursor(self):
        """显示系统鼠标指针"""
        import ctypes as _ct
        try:
            user32 = _ct.windll.user32
            while user32.ShowCursor(True) < 0:
                pass
        except Exception:
            pass

    @property
    def max_particles(self):
        return self._max_particles

    @staticmethod
    def _star_points(cx, cy, r, points=5):
        pts = []
        for i in range(points * 2):
            angle = -math.pi / 2 + math.pi * i / points
            radius = r if i % 2 == 0 else r * 0.4
            pts.append(cx + math.cos(angle) * radius)
            pts.append(cy + math.sin(angle) * radius)
        return pts

