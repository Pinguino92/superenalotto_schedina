#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SuperEnalotto - Generatore di 5 schedine "guidate"
===================================================
✔ Chiavi in mano: esegui `python main.py`

Cosa fa:
1) Scarica l'archivio delle estrazioni da fonti pubbliche (priorità: Lottologia.com; fallback: TuttoSuperEnalotto).
2) Calcola la frequenza di uscita dei numeri 1..90.
3) Genera 5 schedine "guidate" (6 numeri ciascuna) con un criterio ibrido:
   - 3 numeri scelti con peso maggiore tra i più frequenti (top_k).
   - 3 numeri scelti sull'intero intervallo 1..90 (sempre pesati su frequenze).
   - Evita duplicati, ordina i numeri, e cerca di evitare più di due consecutivi.

⚠️ Avvertenza: questo script NON aumenta la probabilità matematica di vincita.
Le estrazioni sono eventi indipendenti; il codice serve solo a gestire dati e produrre combinazioni in modo ordinato.
Gioca responsabilmente.
"""

import io
import re
import sys
import time
import random
import pathlib
import datetime as dt
from typing import List, Optional

import requests
import pandas as pd

START_YEAR = 1997
CURRENT_YEAR = dt.datetime.now().year
YEARS = list(range(START_YEAR, CURRENT_YEAR + 1))
TOP_K = 30
N_SCHEDINE = 5
OUT_DIR = pathlib.Path("output")
SEED = None
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def sessione_http() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    })
    return s

def url_lottologia_xls(year: int) -> str:
    return f"https://www.lottologia.com/superenalotto/archivio-estrazioni/?as=XLS&year={year}"

def tenta_download_lottologia(year: int, sess: requests.Session) -> Optional[bytes]:
    url = url_lottologia_xls(year)
    headers = {"Referer": "https://www.lottologia.com/superenalotto/archivio-estrazioni/"}
    try:
        r = sess.get(url, headers=headers, timeout=30)
        if r.status_code == 200 and r.content and len(r.content) > 1024:
            return r.content
        else:
            return None
    except Exception:
        return None

def tenta_download_tuttosuperenalotto(sess: requests.Session) -> Optional[bytes]:
    url = "https://www.tuttosuperenalotto.it/download-superenalotto.asp?tfile=x&typed=90"
    try:
        r = sess.get(url, timeout=30)
        if r.status_code == 200 and r.content and len(r.content) > 1024:
            return r.content
        return None
    except Exception:
        return None

def _estrai_numeri_da_stringa(s: str):
    import re
    tok = re.findall(r"\d+", str(s))
    nums = [int(t) for t in tok if t.isdigit()]
    nums = [n for n in nums if 1 <= n <= 90]
    if len(nums) >= 6:
        return nums[:6]
    return None

def normalizza_df_sestine(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] >= 6:
        sub = numeric.iloc[:, :6].copy()
        sub.columns = [f"n{{i+1}}" for i in range(6)]
        for c in sub.columns:
            sub[c] = sub[c].astype("Int64")
        sub = sub.dropna()
        sub = sub[(sub >= 1).all(axis=1) & (sub <= 90).all(axis=1)]
        if len(sub) > 0:
            return sub.reset_index(drop=True)
    for col in df.columns:
        if df[col].dtype == object:
            cand = []
            for v in df[col].dropna().astype(str).values:
                nums = _estrai_numeri_da_stringa(v)
                if nums:
                    cand.append(nums[:6])
            if len(cand) >= 1:
                out = pd.DataFrame(cand, columns=[f"n{{i+1}}" for i in range(6)])
                return out
    rows = []
    for _, row in df.iterrows():
        bag = []
        for v in row.values:
            if pd.isna(v):
                continue
            if isinstance(v, (int, float)) and 1 <= int(v) <= 90:
                bag.append(int(v))
            elif isinstance(v, str):
                nums = _estrai_numeri_da_stringa(v)
                if nums:
                    bag.extend(nums)
        bag = [n for n in bag if 1 <= n <= 90]
        if len(bag) >= 6:
            rows.append(bag[:6])
    if rows:
        return pd.DataFrame(rows, columns=[f"n{{i+1}}" for i in range(6)])
    raise ValueError("Impossibile riconoscere le colonne della sestina in questo file.")

def carica_archivi(YEARS):
    sess = sessione_http()
    frames = []
    for y in YEARS:
        log(f"Scarico anno {y} da Lottologia...")
        data = tenta_download_lottologia(y, sess)
        if data is None:
            log("  - Non disponibile (o bloccato).")
            continue
        try:
            df = pd.read_excel(io.BytesIO(data))
            df6 = normalizza_df_sestine(df)
            df6["anno"] = y
            frames.append(df6)
            log(f"  ✓ Anno {y}: {len(df6)} estrazioni lette.")
        except Exception as e:
            log(f"  - Errore parsing anno {y}: {e}")

    if not frames:
        log("Nessun file per anno scaricato. Fallback: archivio corrente da TuttoSuperEnalotto...")
        data = tenta_download_tuttosuperenalotto(sess)
        if data is None:
            raise RuntimeError("Impossibile ottenere dati da nessuna fonte.")
        df = pd.read_excel(io.BytesIO(data))
        df6 = normalizza_df_sestine(df)
        df6["anno"] = dt.datetime.now().year
        frames.append(df6)

    full = pd.concat(frames, ignore_index=True)
    full = full.drop_duplicates(subset=["n1","n2","n3","n4","n5","n6"])
    return full

def calcola_frequenze(df6: pd.DataFrame) -> pd.Series:
    vals = df6[["n1","n2","n3","n4","n5","n6"]].values.flatten()
    ser = pd.Series(vals, dtype="int64")
    freq = ser.value_counts().sort_index()
    full_index = pd.Index(range(1, 91), name="numero")
    freq = freq.reindex(full_index).fillna(0).astype(int)
    return freq

def _weighted_sample_without_replacement(pop, weights, k):
    assert len(pop) == len(weights)
    chosen = []
    pool = list(pop)
    w = list(weights)
    import random
    for _ in range(min(k, len(pool))):
        s = sum(w)
        if s <= 0:
            idx = random.randrange(len(pool))
        else:
            r = random.random() * s
            acc = 0.0
            idx = 0
            for i, wi in enumerate(w):
                acc += wi
                if acc >= r:
                    idx = i
                    break
        chosen.append(pool[idx])
        pool.pop(idx)
        w.pop(idx)
    return chosen

def genera_schedina(freq: pd.Series, top_k: int = TOP_K):
    epsilon = 1e-6
    weights = [float(freq.get(i, 0)) + epsilon for i in range(1, 91)]
    numeri = list(range(1, 91))
    top_sorted = sorted(numeri, key=lambda x: freq.get(x, 0), reverse=True)[:top_k]
    w_top = [weights[i-1] for i in top_sorted]
    sel_top = _weighted_sample_without_replacement(top_sorted, w_top, 3)
    sel_all = _weighted_sample_without_replacement(numeri, weights, 3)
    comb = sorted(set(sel_top + sel_all))
    while len(comb) < 6:
        rest = [n for n in numeri if n not in comb]
        w_rest = [weights[n-1] for n in rest]
        extra = _weighted_sample_without_replacement(rest, w_rest, 1)[0]
        comb.append(extra)
        comb = sorted(set(comb))
    def has_long_run(c):
        c = sorted(c)
        longest = 1
        run = 1
        for i in range(1, len(c)):
            if c[i] == c[i-1] + 1:
                run += 1
                longest = max(longest, run)
            else:
                run = 1
        return longest >= 3
    tries = 0
    while has_long_run(comb) and tries < 10:
        rest = [n for n in numeri if n not in comb]
        w_rest = [weights[n-1] for n in rest]
        swap_in = _weighted_sample_without_replacement(rest, w_rest, 1)[0]
        comb.pop()
        comb.append(swap_in)
        comb = sorted(set(comb))
        tries += 1
    return sorted(comb)[:6]

def genera_schedine(freq: pd.Series, n: int = N_SCHEDINE):
    sched = []
    tentativi = 0
    while len(sched) < n and tentativi < n * 20:
        comb = genera_schedina(freq, TOP_K)
        if comb not in sched:
            sched.append(comb)
        tentativi += 1
    return sched

def main():
    if SEED is not None:
        random.seed(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    yrs = YEARS
    if "--years" in sys.argv:
        try:
            idx = sys.argv.index("--years")
            span = sys.argv[idx+1]
            a, b = span.split("-")
            yrs = list(range(int(a), int(b)+1))
        except Exception:
            log("Formato --years non valido. Uso default.")
    log(f"Scarico archivi anni: {yrs[0]}..{yrs[-1]}")
    df6 = carica_archivi(yrs)
    log(f"Totale estrazioni raccolte: {len(df6)}")
    freq = calcola_frequenze(df6)
    freq_df = pd.DataFrame({"numero": range(1, 91), "frequenza": [int(freq.get(i, 0)) for i in range(1, 91)]})
    freq_df.to_csv(OUT_DIR / "frequenze_superenalotto.csv", index=False)
    df6.to_csv(OUT_DIR / "estrazioni_normalizzate.csv", index=False)
    schedine = genera_schedine(freq, N_SCHEDINE)
    print("\n🎯 5 schedine generate:")
    for i, s in enumerate(schedine, 1):
        print(f"Schedina {i}: {s}")
    xls_path = OUT_DIR / "schedine_superenalotto.xlsx"
    pd.DataFrame(schedine, columns=[f"n{{i}}" for i in range(1,7)]).to_excel(xls_path, index=False)
    log(f"Schedine salvate in: {xls_path}")
    log(f"Frequenze salvate in: {OUT_DIR / 'frequenze_superenalotto.csv'}")
    log(f"Estrazioni normalizzate in: {OUT_DIR / 'estrazioni_normalizzate.csv'}")

if __name__ == "__main__":
    main()
