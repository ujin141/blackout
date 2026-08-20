"""
멤버 데이터를 `assets/js/members.js` 에서 그대로 읽는다.

**파이썬 쪽에 다시 적지 않는다.** 예전에 카드뉴스가 자기 파일에 이름과 장르를
박아 놓는 바람에, 화면에서는 바뀐 멤버가 카드에서는 옛날 것으로 남았습니다.
멤버는 네 곳(members.js · JSON-LD · noscript · llms.txt)을 같이 고치는 규칙인데
파이썬까지 다섯 번째가 되면 반드시 하나를 빼먹습니다.

JS 파일이라 `json.loads` 로는 안 읽힙니다. 우리가 쓰는 형식이 정해져 있어서
(따옴표는 홑따옴표, 키는 따옴표 없음, 주석이 섞임) 필요한 필드만 정규식으로
뽑습니다 — 범용 JS 파서를 붙일 만한 일이 아닙니다.

    from members import MEMBERS, get
    get('LYNN')['genres']['ko']      →  ['EDM', '테크하우스', ...]
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'assets', 'js', 'members.js')

_STR = r"'((?:[^'\\]|\\.)*)'"


def _unq(s):
    return s.replace("\\'", "'").replace('\\\\', '\\')


def _one(block, key):
    m = re.search(rf'\b{key}:\s*{_STR}', block)
    return _unq(m.group(1)) if m else ''


def _lang(block, key):
    """`{ ko: [...], en: [...] }` 또는 `{ ko: '..', en: '..' }` 둘 다 받는다."""
    m = re.search(rf'\b{key}:\s*\{{(.*?)\}}', block, re.S)
    if not m:
        return {'ko': '', 'en': ''}
    body, out = m.group(1), {}
    for lang in ('ko', 'en'):
        arr = re.search(rf'\b{lang}:\s*\[(.*?)\]', body, re.S)
        if arr:
            out[lang] = [_unq(x) for x in re.findall(_STR, arr.group(1))]
            continue
        one = re.search(rf'\b{lang}:\s*{_STR}', body)
        out[lang] = _unq(one.group(1)) if one else ''
    return out


def _parse():
    src = open(SRC, encoding='utf-8').read()
    src = src[src.index('const MEMBERS'):]
    out = []
    # 멤버 하나는 `name:` 에서 다음 `name:` 직전까지. 중괄호를 세는 것보다
    # 이쪽이 주석 안의 중괄호에 안 걸린다
    starts = [m.start() for m in re.finditer(r'^\s*name:\s*\'', src, re.M)]
    for i, a in enumerate(starts):
        b = starts[i + 1] if i + 1 < len(starts) else len(src)
        blk = src[a:b]
        out.append({
            'name': _one(blk, 'name'),
            'role': _lang(blk, 'role'),
            'genres': _lang(blk, 'genres'),
            'bio': _lang(blk, 'bio'),
            'career': _lang(blk, 'career'),
            'instagram': _one(blk, 'instagram'),
            'soundcloud': _one(blk, 'soundcloud'),
            'cutout': _one(blk, 'cutout'),
            'photo': _one(blk, 'photo'),
        })
    return out


MEMBERS = _parse()
BY_NAME = {m['name']: m for m in MEMBERS}


def get(name):
    return BY_NAME[name]


if __name__ == '__main__':
    for m in MEMBERS:
        g = ' · '.join(m['genres']['ko']) or '—'
        print(f"{m['name']:8} {g:44} @{m['instagram'] or '—'}")
