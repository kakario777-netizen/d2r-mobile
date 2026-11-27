#!/usr/bin/env python3
"""엽굵 모드판: 엽굵 treasureclassex.txt → 스위치판 treasureclassex.bin (772바이트 기록).

칸 배치(원본 txt·bin을 맞대어 확인):
  0 이름 char[48] | 48 Picks i32 | 52 group i16 | 54 level i16 | 56 Magic i16 | 58 Rare i16 | 60 Set i16 | 62 Unique i16
  64 (0) | 68 NoDrop i32 | 72 Item1..10 char[64] | 712 Prob1..10 i32 | 752 firstLadderSeason i16 | 754 lastLadderSeason i16
  756 (0) | 760 QuestFlagEx i32 | 764 ConditionCalc 컴파일 번호 i32 (-1 = 없음) | 768 noAlwaysSpawn i32
원본에 없는 아이템 코드·유니크 이름을 가리키는 칸은 뺀다(게임이 못 찾으면 멈출 수 있음).
조건식은 원본에 같은 식이 있을 때만 그 번호를 쓰고, 없으면 원본 행이 있으면 원본 행을 그대로, 없으면 조건 없음.

사용: tc_build.py <원본 excel 폴더> <모드 treasureclassex.txt> <out.bin>
"""
import struct
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import binfer as B


def i(v):
    v = v.strip()
    return int(float(v)) if v else 0


def main(vdir, mtxt, out):
    vh, vr = B.read_txt(f'{vdir}/treasureclassex.txt')
    n, size, recs = B.records(open(f'{vdir}/treasureclassex.bin', 'rb').read())
    assert size == 772 and n == len(vr)
    van = {r[0]: rec for r, rec in zip(vr, recs)}
    vrow = {r[0]: r for r in vr}
    ci = vh.index('ConditionCalc')
    cond = {}
    for r, rec in zip(vr, recs):
        if r[ci]:
            cond[r[ci]] = struct.unpack_from('<i', rec, 764)[0]
    ok = set()
    for t in ('weapons', 'armor', 'misc'):
        th, tr = B.read_txt(f'{vdir}/{t}.txt')
        ok |= {x[th.index('code')] for x in tr}
    for t, col in (('uniqueitems', 'index'), ('setitems', 'index')):
        th, tr = B.read_txt(f'{vdir}/{t}.txt')
        ok |= {x[th.index(col)] for x in tr}
    mh, mr = B.read_txt(mtxt)
    tcs = {r[0] for r in mr}
    vtc = {r[0] for r in vr}
    autos = {v for r in vr for k in range(1, 11) for v in [r[vh.index(f'Item{k}')]] if v and v not in ok and v not in vtc}
    ok |= tcs | autos
    g = {k: mh.index(k) for k in mh}
    outs = []
    dropped = []
    keptvan = []
    # 다른 표(monstats 등)는 드랍 표를 "행 번호 + 161"로 가리킨다 → 원본 행 순서를 그대로 지키고, 새 행은 맨 뒤에 붙인다
    mby = {r[0]: r for r in mr}
    order = [mby.get(vr_[0], None) for vr_ in vr]
    order = [mby[vr_[0]] if vr_[0] in mby else None for vr_ in vr] + [r for r in mr if r[0] not in van]
    for vi, r in enumerate(order):
        if r is None:
            outs.append(recs[vi]); continue
        name = r[0]
        c = r[g['ConditionCalc']]
        if c and c not in cond:
            if name in van:
                outs.append(van[name]); keptvan.append(name); continue
            cidx = -1
        else:
            cidx = cond.get(c, -1) if c else -1
            if c and name in vrow and vrow[name][ci] == c:
                cidx = struct.unpack_from('<i', van[name], 764)[0]
        rec = bytearray(772)
        nm = name.encode('latin-1')[:47]
        rec[0:len(nm)] = nm
        struct.pack_into('<i', rec, 48, i(r[g['Picks']]))
        for k, o in (('group', 52), ('level', 54), ('Magic', 56), ('Rare', 58), ('Set', 60), ('Unique', 62)):
            struct.pack_into('<h', rec, o, i(r[g[k]]))
        struct.pack_into('<i', rec, 68, i(r[g['NoDrop']]))
        for k in range(10):
            it, pr = r[g[f'Item{k + 1}']], i(r[g[f'Prob{k + 1}']])
            if it and it not in ok and not (it.startswith('"gld,mul=') or it.startswith('gld,mul=')):
                dropped.append((name, it)); it, pr = '', 0
            e = it.encode('latin-1')[:63]
            rec[72 + 64 * k:72 + 64 * k + len(e)] = e
            struct.pack_into('<i', rec, 712 + 4 * k, pr)
        struct.pack_into('<h', rec, 752, i(r[g['firstLadderSeason']]))
        struct.pack_into('<h', rec, 754, i(r[g['lastLadderSeason']]))
        struct.pack_into('<i', rec, 760, i(r[g['QuestFlagEx']]))
        struct.pack_into('<i', rec, 764, cidx)
        struct.pack_into('<i', rec, 768, i(r[g['noAlwaysSpawn']]))
        outs.append(bytes(rec))
    open(out, 'wb').write(struct.pack('<I', len(outs)) + b''.join(outs))
    print('rows', len(outs), 'kept vanilla (new condition)', keptvan, 'refs dropped', len(dropped), sorted({d[1] for d in dropped})[:40])


if __name__ == '__main__':
    main(*sys.argv[1:4])
