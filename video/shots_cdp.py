"""
**파티모아 화면을 폰 해상도로 찍는다.** 헤드리스 크롬 + DevTools.

    python shots_cdp.py   →  assets/shots_moon/{home,party,book}.png

## 왜 --screenshot 으로 안 되나

처음 들어온 사람에게 시작 화면(온보딩)이 덮인다. localStorage 의
pm_onboarded 를 보고 판단하는데, 크롬 명령줄로는 그걸 미리 못 넣는다.
DevTools 로 붙어서 넣은 뒤 새로고침한다. 로그인 권유 창도 같은 식
(sessionStorage pm_login_asked).

430×932 를 2.5배로 찍는다. 1075×2330. 피드 칸 안의 폰 목업에 넣으면
충분하다.
"""
import json
import os
import subprocess
import time

import requests
import websocket

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'shots_moon')
PORT = 9333
BASE = 'https://www.partymoa.com'
SHOTS = [
    ('home', '/', None),
    ('party', '/party/after-moon-20260926', None),
    # 예매 시트를 연다. 로그인 권유는 세션 값으로 미리 끈다
    ('book', '/party/after-moon-20260926',
     "(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='예매하기');b&&b.click();return !!b})()"),
]


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, suppress_origin=True)
        self.n = 0

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get('id') == self.n:
                return m.get('result', {})

    def js(self, expr):
        r = self.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        return r.get('result', {}).get('value')


def main():
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(os.environ['TEMP'], 'pm_shots_profile')
    proc = subprocess.Popen([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                             f'--remote-debugging-port={PORT}', f'--user-data-dir={tmp}',
                             '--window-size=430,932', 'about:blank'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                tabs = requests.get(f'http://127.0.0.1:{PORT}/json').json()
                break
            except Exception:
                time.sleep(0.25)
        page = next(t for t in tabs if t['type'] == 'page')
        c = CDP(page['webSocketDebuggerUrl'])
        c.call('Page.enable')
        c.call('Emulation.setDeviceMetricsOverride', width=430, height=932,
               deviceScaleFactor=2.5, mobile=True)
        c.call('Emulation.setUserAgentOverride',
               userAgent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')
        # 같은 출처에서 저장소 값을 넣으려면 먼저 한 번 열어야 한다
        c.call('Page.navigate', url=BASE + '/terms')
        time.sleep(3)
        c.js("localStorage.setItem('pm_onboarded','1'); sessionStorage.setItem('pm_login_asked','1'); sessionStorage.setItem('pm_pc_closed','1'); 1")
        for name, path, click in SHOTS:
            c.call('Page.navigate', url=BASE + path)
            time.sleep(5)
            c.js("window.scrollTo(0,0); 1")
            if click:
                print(name, 'click', c.js(click))
                time.sleep(1.5)
            r = c.call('Page.captureScreenshot', format='png', captureBeyondViewport=False)
            import base64
            with open(os.path.join(OUT, f'{name}.png'), 'wb') as f:
                f.write(base64.b64decode(r['data']))
            print(name, 'ok')
    finally:
        proc.terminate()


if __name__ == '__main__':
    main()
