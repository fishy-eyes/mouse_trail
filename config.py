"""
配置模块 — 管理样式预设和用户设置
"""
import json
import os
import sys

# 预设样式定义
PRESETS = {
    "彩虹": {
        "name": "彩虹",
        "color_mode": "rainbow",       # rainbow | gradient | solid
        "colors": ["#ff0000", "#ff8800", "#ffff00", "#00ff00", "#0088ff", "#8800ff"],
        "particle_size": 6,
        "trail_length": 20,
        "fade_speed": 0.06,
        "line_width": 3,
        "shape": "circle",             # circle | square | star
        "trail_mode": "particle",      # particle | line | both
        "line_style": "uniform",       # uniform | taper
    },
    "烈焰": {
        "name": "烈焰",
        "color_mode": "gradient",
        "colors": ["#ff0000", "#ff4400", "#ff8800", "#ffcc00"],
        "particle_size": 8,
        "trail_length": 18,
        "fade_speed": 0.07,
        "line_width": 4,
        "shape": "circle",
        "trail_mode": "particle",
        "line_style": "uniform",
    },
    "冰霜": {
        "name": "冰霜",
        "color_mode": "gradient",
        "colors": ["#00ccff", "#44ddff", "#88eeff", "#ccffff"],
        "particle_size": 5,
        "trail_length": 22,
        "fade_speed": 0.05,
        "line_width": 2,
        "shape": "square",
        "trail_mode": "particle",
        "line_style": "uniform",
    },
    "霓虹": {
        "name": "霓虹",
        "color_mode": "rainbow",
        "colors": ["#ff00ff", "#00ffff", "#ff00aa", "#aaff00", "#ff6600"],
        "particle_size": 5,
        "trail_length": 25,
        "fade_speed": 0.04,
        "line_width": 3,
        "shape": "circle",
        "trail_mode": "both",
        "line_style": "uniform",
    },
    "银河": {
        "name": "银河",
        "color_mode": "gradient",
        "colors": ["#1a0033", "#330066", "#6600cc", "#9944ff", "#cc88ff"],
        "particle_size": 7,
        "trail_length": 30,
        "fade_speed": 0.03,
        "line_width": 4,
        "shape": "circle",
        "trail_mode": "both",
        "line_style": "uniform",
    },
    "极光": {
        "name": "极光",
        "color_mode": "rainbow",
        "colors": ["#00ff88", "#00ccaa", "#0088cc", "#0044ff", "#8800ff"],
        "particle_size": 6,
        "trail_length": 24,
        "fade_speed": 0.05,
        "line_width": 3,
        "shape": "circle",
        "trail_mode": "particle",
        "line_style": "uniform",
    },
    "纯色-白": {
        "name": "纯色-白",
        "color_mode": "solid",
        "colors": ["#ffffff"],
        "particle_size": 4,
        "trail_length": 12,
        "fade_speed": 0.08,
        "line_width": 2,
        "shape": "circle",
        "trail_mode": "particle",
        "line_style": "uniform",
    },
    "纯色-青": {
        "name": "纯色-青",
        "color_mode": "solid",
        "colors": ["#00ffcc"],
        "particle_size": 5,
        "trail_length": 15,
        "fade_speed": 0.07,
        "line_width": 2,
        "shape": "circle",
        "trail_mode": "particle",
        "line_style": "uniform",
    },
}

DEFAULT_CONFIG = {
    "active_preset": "彩虹",
    "enabled": True,
    "custom_color": "#ff00ff",
    "cursor_enabled": True,
    "cursor_style": "ring",
    "cursor_size": 12,
    "cursor_color": "trail",
    "cursor_image_path": "",
}


def get_app_dir():
    """返回配置文件所在目录：开发时为源码目录，打包后为 exe 所在目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(get_app_dir(), "settings.json")


def load_config():
    """加载用户配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            if cfg.get("active_preset") not in PRESETS:
                cfg["active_preset"] = DEFAULT_CONFIG["active_preset"]
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    """保存用户配置"""
    try:
        clean_cfg = dict(DEFAULT_CONFIG)
        clean_cfg.update(cfg)
        if clean_cfg.get("active_preset") not in PRESETS:
            clean_cfg["active_preset"] = DEFAULT_CONFIG["active_preset"]
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_preset(name):
    """获取指定名称的预设"""
    return PRESETS.get(name, PRESETS["彩虹"])


