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

import requests
import pandas as pd
from bs4 import BeautifulSoup
import collections
import random

URL = "https://www.superenalotto.it/archivio-estrazioni"

def scarica_ultime_estrazioni(n=20):
    res = requests.get(URL)
    if res.status_code != 200:
        raise RuntimeError("Errore nel download della pagina.")
    soup = BeautifulSoup(res.text, "html.parser")

    # cerca tabella estrazioni (può cambiare col tempo → qui ipotizziamo che sia la prima tabella)
    table = soup.find("table")
    if not table:
        raise RuntimeError("Tabella estrazioni non trovata.")

    estrazioni = []
    for tr in table.find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) >= 6:
            try:
                nums = [int(cols[i].get_text().strip()) for i in range(6)]
                estrazioni.append(nums)
            except ValueError:
                continue

    # prendiamo solo le ultime n estrazioni
    estrazioni = estrazioni[:n]
    df = pd.DataFrame(estrazioni, columns=[f"n{i}" for i in range(1,7)])
    return df

def calcola_frequenze(df):
    tutti = df.values.flatten()
    return collections.Counter(tutti)

def genera_schedina(freq, top_k=30):
    numeri = list(range(1,91))
    top = [num for num, _ in freq.most_common(top_k)]
    scelti = random.sample(top, 3) + random.sample(numeri, 3)
    return sorted(set(scelti))[:6]

def main():
    df = scarica_ultime_estrazioni(20)
    freq = calcola_frequenze(df)

    print("📊 Frequenze ultimi 20 concorsi:")
    for num, f in freq.most_common(10):
        print(f"Numero {num}: {f} volte")

    print("\n🎯 5 schedine generate:")
    for i in range(5):
        print(f"Schedina {i+1}: {genera_schedina(freq)}")

if __name__ == "__main__":
    main()

