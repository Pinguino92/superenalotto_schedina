# SuperEnalotto – 5 schedine guidate (chiavi in mano)

> **Nota importante**: non esistono algoritmi che aumentino realmente la probabilità di vincita.
Questo tool serve solo per **analizzare dati storici** e generare schedine **a scopo ricreativo**.
*Gioca responsabilmente.*

## Cosa fa
1. Scarica l'archivio delle estrazioni da fonti pubbliche (priorità **Lottologia.com**, fallback **TuttoSuperEnalotto**).
2. Calcola le **frequenze** di uscita dei numeri 1..90.
3. Genera **5 schedine** (6 numeri) con criterio ibrido: 3 numeri dai più frequenti (top 30), 3 dal set completo, con pesi sulle frequenze.
4. Salva tutto in `output/`:
   - `schedine_superenalotto.xlsx`
   - `frequenze_superenalotto.csv`
   - `estrazioni_normalizzate.csv`

## Requisiti
- **Python 3.10+** (Windows, macOS o Linux)
- Internet attivo

## Installazione (passo passo)
1. Apri il Terminale (Windows: *Prompt dei comandi* o *PowerShell* / macOS: *Terminale*).
2. Entra nella cartella del progetto:  
   `cd superenalotto_schedine_ready`
3. (Opzionale) Crea un ambiente virtuale:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
4. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## Esecuzione immediata
```bash
python main.py
```
- Al termine vedrai le 5 schedine in console e i file nella cartella `output/`.

## Opzioni utili
- Limitare gli anni scaricati (es. solo 2018..2025):
  ```bash
  python main.py --years 2018-2025
  ```
- Rendere i risultati ripetibili (modifica `SEED` dentro `main.py`):
  ```python
  SEED = 1234
  ```

## Fonti dati (verificate al 2025-09-24)
- Archivio + export XLS/TXT per anno: **Lottologia** (pagina “Archivio estrazioni” con pulsanti **XLS/TXT**).
- Archivio download TXT/XLS per anno (selezione su pagina): **TuttoSuperEnalotto**.

> Le pagine potrebbero cambiare struttura o imporre limiti anti-robot. In tal caso, riavvia o riprova più tardi, oppure restringi l'intervallo anni (`--years`).

## Come funziona la generazione
- Calcoliamo la frequenza di ciascun numero 1..90 sullo storico disponibile.
- Ogni schedina:
  - 3 numeri estratti **pesando** tra i più frequenti (top 30).
  - 3 numeri estratti su **1..90** con lo stesso schema di pesi.
  - Evitiamo duplicati e proviamo a ridurre sequenze troppo lunghe di **consecutivi**.

⚠️ Questo **non** altera le probabilità del gioco, che restano fissate e molto basse.

## Supporto rapido
- Errore di parsing? Apri l'Excel scaricato e verifica che contenga 6 numeri per riga; se il sito cambia formato, aggiorna la funzione `normalizza_df_sestine` in `main.py`.
- Connessioni bloccate? Alcuni siti richiedono un *Referer* o limitano il traffico automatico. Riprova più tardi o restringi `--years`.

Buon divertimento!
