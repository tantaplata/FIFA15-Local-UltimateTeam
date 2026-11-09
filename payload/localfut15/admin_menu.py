from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import tkinter as tk
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

ROOT = Path(__file__).resolve().parent
PACKS_TEMPLATE_PATH = ROOT / "pack_settings.json"
CONFIG_PATH = ROOT / "config.json"
LOCAL = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
RUNTIME = LOCAL / "FIFA15LocalFUT"
PACKS_PATH = RUNTIME / "pack_settings.json"
DB_PATH = RUNTIME / "fut15-local.sqlite3"
BACKUPS = RUNTIME / "admin-backups"

PACK_FIELDS = (
    ("name", "Name", str), ("category", "Category", str),
    ("price", "Coin price", int), ("fifa_points", "Points price", int),
    ("size", "Items", int), ("player_slots", "Player slots", int),
    ("club_item_slots", "Club item slots", int), ("rare_slots", "Rare items", int),
    ("player_rare_slots", "Rare players", int),
    ("special_chance", "Special chance (%)", float),
    ("legend_chance", "Legend chance (%)", float),
    ("guaranteed_special_players", "Guaranteed specials", int),
    ("max_special_players", "Max specials", int),
    ("guaranteed_min_rating", "Guaranteed minimum rating", int),
    ("gold_weight", "Gold weight", int), ("silver_weight", "Silver weight", int),
    ("bronze_weight", "Bronze weight", int), ("art_asset_id", "Pack art ID", int),
    ("bio", "Description", str),
)


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".admin.tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def db_connect():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def get_value(key: str, default=0):
    with db_connect() as con:
        row = con.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row[0])
    except Exception:
        return row[0]


def set_value(key: str, value) -> None:
    with db_connect() as con:
        con.execute(
            "INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )


class AdminApp(tk.Tk):
    def __init__(self):
        RUNTIME.mkdir(parents=True, exist_ok=True)
        if not PACKS_PATH.exists() and PACKS_TEMPLATE_PATH.exists():
            shutil.copy2(PACKS_TEMPLATE_PATH, PACKS_PATH)
        super().__init__()
        self.title("Local FUT 15 • Control Centre")
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        window_w = max(900, min(1240, screen_w - 40))
        window_h = max(620, min(790, screen_h - 80))
        self.geometry(f"{window_w}x{window_h}+{max(0, (screen_w-window_w)//2)}+{max(0, (screen_h-window_h)//2)}")
        self.minsize(min(900, window_w), min(620, window_h))
        self.configure(bg="#0b1220")
        self.pack_data = {}
        self.pack_vars: dict[str, tk.Variable] = {}
        self.selected_pack = None
        self.loading_pack = False
        self.pack_save_job = None
        self._style()
        self._build()
        self.refresh_all()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        bg, panel, panel2 = "#0b1220", "#111b2e", "#17233a"
        text, muted, accent = "#f4f7fb", "#93a4bd", "#24d17e"
        s.configure("TFrame", background=bg)
        s.configure("Panel.TFrame", background=panel)
        s.configure("Card.TFrame", background=panel2)
        s.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 10))
        s.configure("Panel.TLabel", background=panel, foreground=text)
        s.configure("Card.TLabel", background=panel2, foreground=text)
        s.configure("Title.TLabel", background=bg, foreground=text, font=("Segoe UI Semibold", 22))
        s.configure("Subtitle.TLabel", background=bg, foreground=muted, font=("Segoe UI", 10))
        s.configure("Section.TLabel", background=bg, foreground=text, font=("Segoe UI Semibold", 14))
        s.configure("Big.TLabel", background=panel2, foreground=text, font=("Segoe UI Semibold", 24))
        s.configure("Metric.TLabel", background=panel2, foreground=muted, font=("Segoe UI", 10))
        s.configure("Status.TLabel", background="#123524", foreground="#70f0ac", padding=(12, 6), font=("Segoe UI Semibold", 9))
        s.configure("TButton", background=panel2, foreground=text, padding=(12, 8), borderwidth=0, font=("Segoe UI Semibold", 9))
        s.map("TButton", background=[("active", "#233552"), ("pressed", "#1b2942")])
        s.configure("Accent.TButton", background=accent, foreground="#06140d", padding=(14, 9), font=("Segoe UI Semibold", 9))
        s.map("Accent.TButton", background=[("active", "#49df97"), ("pressed", "#1ab86c")])
        s.configure("Danger.TButton", background="#512133", foreground="#ffb8ca")
        s.map("Danger.TButton", background=[("active", "#6b2941")])
        s.configure("TNotebook", background=bg, borderwidth=0, tabmargins=(0, 6, 0, 0))
        s.configure("TNotebook.Tab", background=bg, foreground=muted, padding=(18, 10), borderwidth=0, font=("Segoe UI Semibold", 10))
        s.map("TNotebook.Tab", background=[("selected", panel)], foreground=[("selected", text), ("active", text)])
        s.configure("TLabelframe", background=panel, foreground=text, bordercolor="#263652", relief="solid")
        s.configure("TLabelframe.Label", background=panel, foreground=text, font=("Segoe UI Semibold", 11))
        s.configure("TEntry", fieldbackground="#0d1728", foreground=text, insertcolor=text, bordercolor="#2b3d5c", padding=(8, 7))
        s.map("TEntry", bordercolor=[("focus", accent)])
        s.configure("TCheckbutton", background=panel, foreground=text, padding=4)
        s.map("TCheckbutton", background=[("active", panel)])
        s.configure("Treeview", background="#0d1728", fieldbackground="#0d1728", foreground=text, rowheight=31, borderwidth=0)
        s.configure("Treeview.Heading", background=panel2, foreground=muted, relief="flat", padding=(8, 8), font=("Segoe UI Semibold", 9))
        s.map("Treeview", background=[("selected", "#1b6b50")], foreground=[("selected", "#ffffff")])
        s.map("Treeview.Heading", background=[("active", "#22334f")])

    def _build(self):
        top = ttk.Frame(self, padding=(24, 18, 24, 12))
        top.pack(fill="x")
        brand = ttk.Frame(top)
        brand.pack(side="left")
        ttk.Label(brand, text="LOCAL FUT 15", style="Title.TLabel").pack(anchor="w")
        ttk.Label(brand, text="Offline club, economy and pack control centre", style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))
        self.status = ttk.Label(top, text="Ready", style="Status.TLabel")
        self.status.pack(side="right")
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        self._dashboard_tab()
        self._packs_tab()
        self._server_tab()
        self._tools_tab()

    def _dashboard_tab(self):
        tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=22)
        self.tabs.add(tab, text="  Overview  ")
        ttk.Label(tab, text="Club overview", style="Panel.TLabel", font=("Segoe UI Semibold", 15)).pack(anchor="w", pady=(0, 14))
        cards = ttk.Frame(tab)
        cards.pack(fill="x")
        cards.columnconfigure((0, 1), weight=1)
        coin_card = ttk.Frame(cards, style="Card.TFrame", padding=20)
        coin_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(coin_card, text="COIN BALANCE", style="Metric.TLabel").pack(anchor="w")
        self.coins_label = ttk.Label(coin_card, style="Big.TLabel")
        self.coins_label.pack(anchor="w", pady=(5, 0))
        point_card = ttk.Frame(cards, style="Card.TFrame", padding=20)
        point_card.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(point_card, text="FIFA POINTS", style="Metric.TLabel").pack(anchor="w")
        self.points_label = ttk.Label(point_card, style="Big.TLabel")
        self.points_label.pack(anchor="w", pady=(5, 0))
        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=12)
        for text, key, mode in (
            ("Set coins", "credits", "set"), ("Add coins", "credits", "add"),
            ("Set FIFA Points", "fifa_points", "set"), ("Add FIFA Points", "fifa_points", "add"),
        ):
            ttk.Button(btns, text=text, command=lambda k=key, m=mode: self.change_balance(k, m), style="Accent.TButton" if mode == "add" else "TButton").pack(side="left", padx=(0, 8))
        identity = ttk.LabelFrame(tab, text="Club identity", padding=14)
        identity.pack(fill="x", pady=15)
        self.identity_vars = {}
        for row, (key, label) in enumerate((("club_name", "Club name"), ("club_abbr", "Abbreviation"), ("persona_name", "Manager name"))):
            ttk.Label(identity, text=label, width=18).grid(row=row, column=0, sticky="w", pady=4)
            v = tk.StringVar(); self.identity_vars[key] = v
            ttk.Entry(identity, textvariable=v, width=42).grid(row=row, column=1, sticky="ew", pady=4)
        identity.columnconfigure(1, weight=1)
        ttk.Button(identity, text="Save identity live", command=self.save_identity, style="Accent.TButton").grid(row=3, column=1, sticky="e", pady=(12, 0))
        rewards = ttk.LabelFrame(tab, text="Daily reward", padding=14)
        rewards.pack(fill="x", pady=(2, 10))
        self.reward_title = ttk.Label(rewards, text="Checking reward…", style="Panel.TLabel", font=("Segoe UI Semibold", 12))
        self.reward_title.pack(side="left", anchor="w")
        self.reward_detail = ttk.Label(rewards, text="", style="Panel.TLabel")
        self.reward_detail.pack(side="left", padx=14)
        self.reward_button = ttk.Button(rewards, text="Claim reward pack", command=self.claim_daily_reward, style="Accent.TButton")
        self.reward_button.pack(side="right")
        ttk.Label(tab, text="Changes are written to the active local save. Leave FUT and enter it again to refresh the in-game header.", style="Panel.TLabel", wraplength=850).pack(anchor="w", pady=10)

    def _packs_tab(self):
        tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=14)
        self.tabs.add(tab, text="  Pack Studio  ")
        tab.columnconfigure(0, weight=2, minsize=330)
        tab.columnconfigure(1, weight=3, minsize=460)
        tab.rowconfigure(0, weight=1)
        left = ttk.Frame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.pack_tree = ttk.Treeview(left, columns=("id", "name", "coins", "points", "on"), show="headings", height=16)
        for col, title, width in (("id", "ID", 45), ("name", "Pack", 210), ("coins", "Coins", 75), ("points", "Points", 70), ("on", "On", 40)):
            self.pack_tree.heading(col, text=title); self.pack_tree.column(col, width=width, anchor="w")
        self.pack_tree.pack(fill="both", expand=True)
        self.pack_tree.bind("<<TreeviewSelect>>", self.select_pack)
        lb = ttk.Frame(left); lb.pack(fill="x", pady=8)
        ttk.Button(lb, text="New pack", command=self.new_pack, style="Accent.TButton").pack(side="left")
        ttk.Button(lb, text="Duplicate", command=self.duplicate_pack).pack(side="left", padx=4)
        ttk.Button(lb, text="Delete", command=self.delete_pack, style="Danger.TButton").pack(side="left")
        right = ttk.LabelFrame(tab, text="Selected pack", padding=12)
        right.grid(row=0, column=1, sticky="nsew")
        top_actions = ttk.Frame(right)
        top_actions.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 6))
        ttk.Button(top_actions, text="Save now", command=self.save_pack, style="Accent.TButton").pack(side="right")
        ttk.Button(top_actions, text="All Special Players preset", command=self.all_special_preset).pack(side="right", padx=6)
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="Visible/enabled in store", variable=self.enabled_var, command=self.schedule_pack_save).grid(row=1, column=0, columnspan=4, sticky="w", pady=4)
        for index, (key, label, typ) in enumerate(PACK_FIELDS):
            row = 2 + index // 2
            column = (index % 2) * 2
            ttk.Label(right, text=label).grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
            v = tk.StringVar(); self.pack_vars[key] = v
            ent = ttk.Entry(right, textvariable=v)
            ent.grid(row=row, column=column+1, sticky="ew", padx=(0, 12), pady=4)
            ent.bind("<FocusOut>", lambda _e: self.schedule_pack_save())
            ent.bind("<Return>", lambda _e: self.save_pack())
        right.columnconfigure(1, weight=1)
        right.columnconfigure(3, weight=1)
        final_row = 2 + (len(PACK_FIELDS) + 1) // 2
        action = ttk.Frame(right); action.grid(row=final_row, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        ttk.Button(action, text="Save pack live", command=self.save_pack, style="Accent.TButton").pack(side="right")
        ttk.Button(action, text="Reload", command=self.load_packs).pack(side="right", padx=6)
        ttk.Label(right, text="Minimum rating guarantees at least one player at or above that rating. Use 0 to disable it.", wraplength=650).grid(row=final_row+1, column=0, columnspan=4, sticky="w", pady=10)

    def _server_tab(self):
        tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=24)
        self.tabs.add(tab, text="  Server  ")
        ttk.Label(tab, text="Server settings", style="Panel.TLabel", font=("Segoe UI Semibold", 15)).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        self.config_vars = {}
        options = (
            ("ai_market_enabled", "Enable AI Transfer Market", "bool"),
            ("offline_seasons_enabled", "Enable Offline Seasons", "bool"),
            ("ai_market_fast_sales_seconds", "Seconds before AI buys listings", "int"),
            ("ai_market_copies_per_card", "AI listings per card", "int"),
            ("ai_market_results", "Market result limit (0 = full)", "int"),
            ("debug_unknown_http", "Verbose request logging", "bool"),
        )
        for row, (key, label, typ) in enumerate(options, 1):
            ttk.Label(tab, text=label, width=34).grid(row=row, column=0, sticky="w", pady=7)
            if typ == "bool":
                v = tk.BooleanVar(); ttk.Checkbutton(tab, variable=v).grid(row=row, column=1, sticky="w")
            else:
                v = tk.StringVar(); ttk.Entry(tab, textvariable=v, width=20).grid(row=row, column=1, sticky="w")
            self.config_vars[key] = (v, typ)
        ttk.Button(tab, text="Save server settings", command=self.save_config, style="Accent.TButton").grid(row=len(options)+1, column=1, sticky="w", pady=15)
        ttk.Label(tab, text="Pack and balance controls are live. Core market/server settings apply the next time Local FUT starts.", style="Panel.TLabel", wraplength=720).grid(row=len(options)+2, column=0, columnspan=2, sticky="w")

    def _tools_tab(self):
        tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=24)
        self.tabs.add(tab, text="  Tools  ")
        ttk.Label(tab, text="Backups & maintenance", style="Panel.TLabel", font=("Segoe UI Semibold", 15)).pack(anchor="w", pady=(0, 14))
        ttk.Button(tab, text="Back up local club now", command=self.backup_db, style="Accent.TButton").pack(anchor="w", pady=6)
        ttk.Button(tab, text="Open Local FUT data folder", command=lambda: os.startfile(RUNTIME)).pack(anchor="w", pady=6)
        ttk.Button(tab, text="Open server logs", command=lambda: os.startfile(RUNTIME / "logs")).pack(anchor="w", pady=6)
        ttk.Button(tab, text="Delete club and start fresh", command=self.reset_club, style="Danger.TButton").pack(anchor="w", pady=6)
        ttk.Label(
            tab,
            text="Creates a backup, closes FIFA, stops the local server, then removes only the Local FUT club save.",
            style="Panel.TLabel",
        ).pack(anchor="w", pady=(0, 10))
        self.db_stats = ttk.Label(tab, text="", justify="left")
        self.db_stats.pack(anchor="w", pady=20)

    def notify(self, text: str):
        self.status.config(text=text)
        self.after(4500, lambda: self.status.config(text="Ready"))

    def refresh_all(self):
        self.refresh_dashboard(); self.load_packs(); self.load_config(); self.refresh_stats(); self.refresh_daily_reward()

    def refresh_dashboard(self):
        self.coins_label.config(text=f"{int(get_value('credits', 0)):,}")
        self.points_label.config(text=f"{int(get_value('fifa_points', 0)):,}")
        defaults = read_json(CONFIG_PATH, {})
        for key, var in self.identity_vars.items():
            var.set(str(get_value(key, defaults.get(key, ""))))

    def _reward_request(self, method="GET"):
        info = read_json(RUNTIME / "runtime_ports.json", {})
        port = int(info.get("fut_port", 8199) or 8199)
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/local-admin/rewards/daily",
            data=b"{}" if method == "POST" else None,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))

    def refresh_daily_reward(self):
        try:
            status = self._reward_request()
        except (OSError, ValueError, urllib.error.URLError):
            self.reward_title.config(text="Start Local FUT to claim")
            self.reward_detail.config(text="The reward service is currently offline")
            self.reward_button.state(["disabled"])
            return
        claimed = bool(status.get("claimedToday", False))
        streak = int(status.get("streak", 0) or 0)
        self.reward_title.config(text="Claimed today" if claimed else str(status.get("packName", "Daily Pack")))
        self.reward_detail.config(text=f"Login streak: {streak} day{'s' if streak != 1 else ''}")
        self.reward_button.state(["disabled"] if claimed else ["!disabled"])

    def claim_daily_reward(self):
        try:
            result = self._reward_request("POST")
        except (OSError, ValueError, urllib.error.URLError) as exc:
            messagebox.showerror("Reward service unavailable", f"Start Local FUT, then try again.\n\n{exc}")
            return
        if result.get("claimed"):
            self.refresh_daily_reward()
            messagebox.showinfo(
                "Daily reward claimed",
                f"You received: {result.get('packName', 'Reward Pack')}\n\n"
                "The cards are waiting in Unassigned Items. Re-enter FUT if they do not appear immediately.",
            )
            return
        if result.get("reason") == "unassigned_items":
            messagebox.showwarning("Clear Unassigned Items", "Deal with your current Unassigned Items before claiming today's reward.")
        else:
            messagebox.showinfo("Already claimed", "Today's reward pack has already been claimed.")
        self.refresh_daily_reward()

    def change_balance(self, key, mode):
        amount = simpledialog.askinteger("Balance", "Enter amount:", parent=self, minvalue=0, maxvalue=2_000_000_000)
        if amount is None: return
        value = amount if mode == "set" else int(get_value(key, 0)) + amount
        set_value(key, value); self.refresh_dashboard(); self.notify("Balance updated")

    def save_identity(self):
        name = self.identity_vars["club_name"].get().strip()[:30]
        abbr = self.identity_vars["club_abbr"].get().strip().upper()[:3]
        persona = self.identity_vars["persona_name"].get().strip()[:30]
        if not name or not abbr or not persona:
            messagebox.showerror("Invalid identity", "All three identity fields are required."); return
        set_value("club_name", name); set_value("club_abbr", abbr); set_value("persona_name", persona)
        self.notify("Club identity saved")

    def load_packs(self):
        self.pack_data = read_json(PACKS_PATH, {"next_pack_id": 40, "packs": {}})
        packs = self.pack_data.setdefault("packs", {})
        retired = []
        for pid, pack in list(packs.items()):
            raw_ids = pack.get("guaranteed_resource_ids", []) or []
            has_retired_id = any(str(value) == "167792961" for value in raw_ids)
            if "josh 99" in str(pack.get("name", "")).lower() or has_retired_id:
                retired.append(pid)
                packs.pop(pid, None)
        if retired:
            write_json(PACKS_PATH, self.pack_data)
        self.pack_tree.delete(*self.pack_tree.get_children())
        for pid, p in sorted(self.pack_data.get("packs", {}).items(), key=lambda x: int(x[0])):
            self.pack_tree.insert("", "end", iid=str(pid), values=(pid, p.get("name", "Pack"), p.get("price", 0), p.get("fifa_points", 0), "Yes" if p.get("enabled", True) else "No"))

    def select_pack(self, _event=None):
        sel = self.pack_tree.selection()
        if not sel: return
        self.loading_pack = True
        self.selected_pack = sel[0]; p = self.pack_data["packs"][self.selected_pack]
        self.enabled_var.set(bool(p.get("enabled", True)))
        for key, _, _ in PACK_FIELDS:
            value = p.get(key, "")
            if key in ("special_chance", "legend_chance") and value != "": value = float(value) * 100
            self.pack_vars[key].set(str(value))
        self.loading_pack = False

    def schedule_pack_save(self):
        if self.loading_pack or self.selected_pack is None: return
        if self.pack_save_job is not None: self.after_cancel(self.pack_save_job)
        self.pack_save_job = self.after(650, lambda: self.save_pack(silent=True))

    def save_pack(self, silent=False):
        self.pack_save_job = None
        if self.selected_pack is None:
            if not silent: messagebox.showinfo("Select a pack", "Choose a pack first.")
            return
        p = dict(self.pack_data["packs"][self.selected_pack]); p["enabled"] = bool(self.enabled_var.get())
        try:
            for key, _, typ in PACK_FIELDS:
                raw = self.pack_vars[key].get().strip()
                if raw != "": p[key] = typ(raw) / 100.0 if key in ("special_chance", "legend_chance") else typ(raw)
            size = int(p.get("size", 12)); players = int(p.get("player_slots", 0)); clubs = int(p.get("club_item_slots", 0))
            if not 1 <= size <= 30 or players < 0 or clubs < 0 or players + clubs > size: raise ValueError("Player + club slots cannot exceed pack size (1–30).")
            chance = float(p.get("special_chance", 0));
            if not 0 <= chance <= 1: raise ValueError("Special chance must be between 0% and 100%.")
            legend_chance = float(p.get("legend_chance", 0) or 0)
            if not 0 <= legend_chance <= 1: raise ValueError("Legend chance must be between 0% and 100%.")
            guaranteed = int(p.get("guaranteed_special_players", 0) or 0)
            max_specials = int(p.get("max_special_players", 0) or 0)
            minimum_rating = int(p.get("guaranteed_min_rating", 0) or 0)
            if guaranteed < 0 or guaranteed > players: raise ValueError("Guaranteed specials cannot exceed player slots.")
            if max_specials < guaranteed: raise ValueError("Max specials must be at least the guaranteed-special count.")
            if minimum_rating and not 40 <= minimum_rating <= 99: raise ValueError("Minimum rating must be 0 (off) or between 40 and 99.")
        except ValueError as exc:
            if not silent: messagebox.showerror("Invalid pack", str(exc))
            return
        self.pack_data["packs"][self.selected_pack] = p; write_json(PACKS_PATH, self.pack_data)
        self.load_packs(); self.pack_tree.selection_set(self.selected_pack); self.select_pack(); self.notify("Pack saved live")

    def all_special_preset(self):
        if self.selected_pack is None:
            children = self.pack_tree.get_children()
            if not children:
                messagebox.showerror("No packs", "No pack definitions were found."); return
            self.selected_pack = str(children[0])
        p = dict(self.pack_data["packs"][self.selected_pack])
        try: size = max(1, min(30, int(p.get("size", 12) or 12)))
        except ValueError: size = 12
        p.update({"size":size, "player_slots":size, "club_item_slots":0,
                  "rare_slots":size, "player_rare_slots":size,
                  "special_chance":1.0, "guaranteed_special_players":size,
                  "max_special_players":size, "gold_weight":100,
                  "silver_weight":0, "bronze_weight":0})
        self.pack_data["packs"][self.selected_pack] = p
        write_json(PACKS_PATH, self.pack_data)
        pid = self.selected_pack
        self.load_packs(); self.pack_tree.selection_set(pid); self.pack_tree.see(pid); self.select_pack()
        self.notify(f"Pack {pid} saved: {size} guaranteed special players")
        messagebox.showinfo("Preset saved", f"Pack {pid} now guarantees {size} special players. Open a new pack in FUT.")

    def new_pack(self):
        pid = str(max([int(x) for x in self.pack_data.get("packs", {})] + [39]) + 1)
        self.pack_data.setdefault("packs", {})[pid] = {"enabled": True, "category":"promo", "name":"Custom Pack", "bio":"A custom Local FUT pack.", "price":125000, "fifa_points":2500, "size":12, "player_slots":12, "club_item_slots":0, "gold_weight":100, "silver_weight":0, "bronze_weight":0, "rare_slots":12, "player_rare_slots":12, "special_chance":0.10, "legend_chance":0.01, "guaranteed_special_players":1, "max_special_players":2, "guaranteed_min_rating":0, "art_asset_id":7}
        self.pack_data["next_pack_id"] = int(pid) + 1; write_json(PACKS_PATH, self.pack_data); self.load_packs(); self.pack_tree.selection_set(pid); self.pack_tree.see(pid); self.select_pack()

    def duplicate_pack(self):
        if self.selected_pack is None: return
        source = dict(self.pack_data["packs"][self.selected_pack]); self.new_pack()
        source["name"] = str(source.get("name", "Pack")) + " Copy"; self.pack_data["packs"][self.selected_pack] = source
        write_json(PACKS_PATH, self.pack_data); self.load_packs(); self.pack_tree.selection_set(self.selected_pack); self.select_pack()

    def delete_pack(self):
        if self.selected_pack is None or not messagebox.askyesno("Delete pack", "Remove this pack from the store?"): return
        del self.pack_data["packs"][self.selected_pack]; write_json(PACKS_PATH, self.pack_data); self.selected_pack=None; self.load_packs(); self.notify("Pack deleted")

    def load_config(self):
        cfg = read_json(CONFIG_PATH, {})
        for key, (var, typ) in self.config_vars.items(): var.set(bool(cfg.get(key, False)) if typ == "bool" else str(cfg.get(key, 0)))

    def save_config(self):
        cfg = read_json(CONFIG_PATH, {})
        try:
            for key, (var, typ) in self.config_vars.items(): cfg[key] = bool(var.get()) if typ == "bool" else int(var.get())
        except ValueError:
            messagebox.showerror("Invalid setting", "Number settings must contain whole numbers."); return
        write_json(CONFIG_PATH, cfg); self.notify("Settings saved — restart Local FUT to apply")

    def backup_db(self):
        if not DB_PATH.exists(): messagebox.showinfo("No save", "The local club has not been created yet."); return
        target = self._create_backup()
        self.notify(f"Backup created: {target.name}")

    def _create_backup(self) -> Path:
        BACKUPS.mkdir(parents=True, exist_ok=True); target = BACKUPS / f"fut15-local-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
        src = sqlite3.connect(DB_PATH, timeout=10); dst = sqlite3.connect(target)
        try: src.backup(dst)
        finally: dst.close(); src.close()
        return target

    def _stop_local_fut(self) -> None:
        subprocess.run(
            ["taskkill", "/IM", "fifa15.exe", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        runtime_info = read_json(RUNTIME / "runtime_ports.json", {})
        try:
            server_pid = int(runtime_info.get("server_pid", 0) or 0)
        except (TypeError, ValueError):
            server_pid = 0
        if server_pid > 0:
            subprocess.run(
                ["taskkill", "/PID", str(server_pid), "/F", "/T"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        script = (
            "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
            "Where-Object { $_.Name -like 'python*.exe' "
            "-and $_.CommandLine -like '*localfut15*server.py*' } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        # A forced stop can return just before SQLite releases its Windows file
        # handles. Wait for both the recorded PID and the WAL lock to disappear.
        for _ in range(50):
            running = False
            if server_pid > 0:
                probe = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {server_pid}", "/NH"],
                    capture_output=True, text=True, check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                running = str(server_pid) in probe.stdout
            if not running:
                break
            time.sleep(0.1)

    def reset_club(self):
        if not DB_PATH.exists():
            messagebox.showinfo("No club", "There is no Local FUT club to delete.")
            return
        if not messagebox.askyesno(
            "Delete Local FUT club?",
            "This will close FIFA, stop the local server and delete your current Local FUT club.\n\n"
            "Coins, players, squads and progress will be reset. A dated backup will be created first.\n\nContinue?",
            icon="warning",
        ):
            return
        try:
            backup = self._create_backup()
            self._stop_local_fut()
            last_error = None
            for _ in range(15):
                try:
                    for suffix in ("-wal", "-shm", ""):
                        Path(str(DB_PATH) + suffix).unlink(missing_ok=True)
                    last_error = None
                    break
                except PermissionError as exc:
                    last_error = exc
                    time.sleep(0.2)
            if last_error:
                raise last_error
            (RUNTIME / "runtime_ports.json").unlink(missing_ok=True)
            self.refresh_all()
            self.notify("Club deleted — launch Local FUT to create a new one")
            messagebox.showinfo(
                "Club deleted",
                f"Your Local FUT club was deleted successfully.\n\nBackup: {backup.name}\n\n"
                "Run PLAY_LOCAL_FUT15.cmd to create a fresh club.",
            )
        except (PermissionError, sqlite3.Error, OSError) as exc:
            messagebox.showerror("Could not delete club", f"The club could not be deleted safely.\n\n{exc}")

    def refresh_stats(self):
        if not DB_PATH.exists(): self.db_stats.config(text="No Local FUT save exists yet."); return
        try:
            with db_connect() as con:
                tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                items = con.execute("SELECT COUNT(*) FROM items").fetchone()[0] if "items" in tables else 0
                auctions = con.execute("SELECT COUNT(*) FROM auctions").fetchone()[0] if "auctions" in tables else 0
            self.db_stats.config(text=f"Save: {DB_PATH}\nClub items: {items:,}\nAuction records: {auctions:,}")
        except sqlite3.Error as exc: self.db_stats.config(text=f"Save temporarily busy: {exc}")


if __name__ == "__main__":
    AdminApp().mainloop()
