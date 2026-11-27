#!/usr/bin/env python3
"""엽굵 모드판: 게임 수치 표(txt)를 게임이 읽는 bin으로 바꾸는 도구.

bin = [행 수 u32] + 고정 크기 기록 × 행 수. 칸 위치는 원본 txt와 원본 bin을 맞대어 자동으로 알아낸다
(문자열 칸은 char[N], 숫자 칸은 1/2/4바이트 정수). 알아내지 못한 칸(게임이 계산해 넣는 값 등)은
같은 이름의 원본 행에서 그대로 가져온다.

사용: binfer.py infer <vanilla.txt> <vanilla.bin>           → 칸 배치 출력
      binfer.py build <vanilla.txt> <vanilla.bin> <mod.txt> <out.bin>
"""
import struct
import sys


def read_txt(p):
    raw = open(p, 'rb').read().decode('latin-1')
    lines = [l.rstrip('\r') for l in raw.split('\n')]
    head = lines[0].split('\t')
    rows = []
    for l in lines[1:]:
        if not l.strip():
            continue
        c = l.split('\t')
        c += [''] * (len(head) - len(c))
        if c[0] == 'Expansion' and not any(x.strip() for x in c[1:]):
            continue
        rows.append(c)
    return head, rows


def records(b):
    n = struct.unpack_from('<I', b, 0)[0]
    size = (len(b) - 4) // n
    return n, size, [b[4 + i * size:4 + (i + 1) * size] for i in range(n)]


def as_int(s):
    s = s.strip()
    if s == '':
        return 0
    try:
        return int(s)
    except ValueError:
        try:
            f = float(s)
            return int(f) if f == int(f) else None
        except ValueError:
            return None


def infer(head, rows, recs, size):
    """칸마다 (종류, 위치, 크기) 찾기. 종류: 's' 문자열 / 'i' 부호 정수 / 'u' 부호 없는 정수"""
    n = len(rows)
    lay = {}
    used = set()
    for ci, name in enumerate(head):
        vals = [r[ci] for r in rows]
        if not any(v.strip() for v in vals):
            continue
        nums = [as_int(v) for v in vals]
        found = None
        if all(x is not None for x in nums):
            for w, fmt in ((4, '<i'), (2, '<h'), (1, '<b'), (2, '<H'), (1, '<B'), (4, '<I')):
                for o in range(0, size - w + 1):
                    if any(k in used for k in range(o, o + w)):
                        continue
                    ok = True
                    for i in range(n):
                        v = nums[i]
                        try:
                            if struct.unpack_from(fmt, recs[i], o)[0] != v:
                                ok = False
                                break
                        except struct.error:
                            ok = False
                            break
                    if ok:
                        found = ('i', o, w, fmt)
                        break
                if found:
                    break
        if not found:
            enc = [v.encode('latin-1') for v in vals]
            mx = max(len(e) for e in enc)
            for o in range(0, size - mx):
                if any(k in used for k in range(o, o + mx + 1)):
                    continue
                if all(recs[i][o:o + len(enc[i]) + 1] == enc[i] + b'\0' for i in range(n)):
                    end = o + mx + 1
                    while end < size and end - o < 256 and all(recs[i][end] == 0 for i in range(n)):
                        end += 1
                    found = ('s', o, end - o, None)
                    break
        if found:
            lay[name] = found
            t, o, w, _ = found
            used.update(range(o, o + (w if t == 'i' else len(max((v.encode('latin-1') for v in vals), key=len)) + 1)))
    return lay


def build(vtxt, vbin, mtxt, out):
    head, rows = read_txt(vtxt)
    n, size, recs = records(open(vbin, 'rb').read())
    assert n == len(rows), (n, len(rows))
    lay = infer(head, rows, recs, size)
    mhead, mrows = read_txt(mtxt)
    key = head[0]
    byname = {}
    for r, rec in zip(rows, recs):
        byname.setdefault(r[0], rec)
    blank = bytes(size)
    outs = []
    miss = []
    for r in mrows:
        d = dict(zip(mhead, r))
        rec = bytearray(byname.get(r[0], recs[-1] if False else blank))
        if r[0] not in byname:
            rec = bytearray(recs[0])   # 새 행: 첫 원본 행을 바탕으로 알려진 칸을 모두 덮어씀
            for name, (t, o, w, fmt) in lay.items():
                rec[o:o + w] = b'\0' * w
        for name, (t, o, w, fmt) in lay.items():
            if name not in d:
                continue
            v = d[name]
            if t == 'i':
                x = as_int(v)
                if x is None:
                    miss.append((r[0], name, v))
                    continue
                try:
                    struct.pack_into(fmt, rec, o, x)
                except struct.error:
                    miss.append((r[0], name, v))
            else:
                e = v.encode('latin-1')[:w - 1]
                rec[o:o + w] = e + b'\0' * (w - len(e))
        outs.append(bytes(rec))
    lost = [h for h in mhead if h not in lay and h.strip() and not h.startswith('*')]
    open(out, 'wb').write(struct.pack('<I', len(outs)) + b''.join(outs))
    return lay, miss, lost, len(outs)


if __name__ == '__main__':
    if sys.argv[1] == 'infer':
        h, r = read_txt(sys.argv[2])
        n, size, recs = records(open(sys.argv[3], 'rb').read())
        lay = infer(h, r, recs, size)
        print('rows', n, 'size', size, 'found', len(lay), '/', len(h))
        for k, v in sorted(lay.items(), key=lambda x: x[1][1]):
            print(f'{v[1]:5} {v[0]}{v[2]:<4} {k}')
        print('missing:', [k for k in h if k not in lay])
    else:
        lay, miss, lost, cnt = build(*sys.argv[2:6])
        print('rows', cnt, 'cols', len(lay), 'bad values', miss[:10], 'columns not placed', lost)
