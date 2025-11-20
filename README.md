
# 🍝 What2It — Smart Fridge Recommender

Un'applicazione di prototipo per suggerire ricette basate sugli ingredienti disponibili ("what's in the fridge").
Questo repository include i dati di ricette italiane, script per popolare un database PostgreSQL, una semplice interfaccia Streamlit multi-pagina e un modulo di raccomandazione che combina filtri basati sul contenuto (TF‑IDF + cosine similarity) e regole di preferenza dell'utente.

## Panoramica

Caratteristiche principali:
- Importazione e popolamento schema DB (PostgreSQL) da CSV del dataset di ricette italiane.
- Interfaccia Streamlit per: login/registrazione, gestione ingredienti in frigo, suggerimenti di ricette e lista ricette preferite.
- Motore di similarità contenutistico basato su TF‑IDF (ingredienti + titolo + categoria) e cosine similarity.
- Integrazione ibrida: ranking basato su percentuale di ingredienti posseduti e similarità con ricette preferite.

## 📁 Struttura del Progetto
```txt
what2it/
├── data/						# Dataset in formato csv per il popolamento del DB
├── database/
	├── database_setup.sql			# Script SQL per la definizione dello schema del DB
	├── populate_database.py		# Script per la creazione ed il popolamento del DB       
├── images/        				# Immagini delle ricette               
├── streamlit/                    
    ├── pages/
		├── Gestione_Ingredienti.py			# Interfaccia per aggiungere, modificare e gestire gli ingredienti
		├── In_Cerca_Di_Ispirazione			# Pagina di ricerca ricette suggerite in base agli ingredienti
		├── Le_Tue_Ricette_Preferite.py		# Pagina contenente le ricette salvate tra i preferiti dall’utente
	├── recommendation/
		├── pycache/						# Cache auto-generata da Python (non modificare)
		├── compute_item_similarity          # Modulo di raccomandazione basato su similarità tra ricette  
	├── Login.py             
├── start-all.sh				# Script per avvio completo dell’ambiente e dell’applicazione
├── start-streamlit.sh			# Script rapido per avviare solo l’app Streamlit
├── relazione/
    ├── relazione.pdf/            # Relazione del progetto implementato

```

## Requisiti e Ambiente

- Python 3.10+
- PostgreSQL (versione moderna) se si usa lo script `populate_database.py`.
- Dipendenze elencate in `requirements.txt` (installare in un virtualenv).

## Installazione locale (sintetico)

1. Crea e attiva un virtualenv (es. venv) e scarica le dipendenze:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Configura le variabili d'ambiente per la connessione al DB, creando un file .env nella root del progetto:

```bash
PGUSER=user
PGPASSWORD=password
PGDATABASE=db_name
PGHOST=localhost
PGPORT=5432
```

3. Esegui lo script per l'avvio completo dell'ambiente e dell'applicazione.

```bash
chmod +x start-all.sh
./start-all.sh
```
Tale script provvede alla creazione e popolamento del database ed all'avvio dell'interfaccia web streamlit.

Note:

In seguito al primo avvio dell'applicazione (DB già esistente) si può avviare l'interfaccia web con l'esecuzione di un'ulteriore script

```bash
chmod +x start-streamlit.sh
./start-streamlit.sh
```

## Popolare il database (PostgreSQL)

Lo script `populate_database.py` è pensato per creare il DB (se non esiste), applicare lo schema (`database_setup.sql`) e importare i CSV presenti in `data/processed/italian gastronomic recipes dataset/foods/CSV/`.

I passaggi principali:

1. Assicurati che i file CSV richiesti esistano:
	 - `ingredientsMetaclasses.csv`
	 - `ingredientsClasses.csv`
	 - `ingredients.csv`
	 - `recipes.csv`

2. Esegui lo script (dalla root del progetto):

```bash
python database/populate_database.py
```

Lo script esegue (in ordine):
- verifica presenza CSV
- crea il database (se necessario)
- esegue `database_setup.sql` per creare le tabelle
- importa i CSV con `COPY` (ottimizzato per dati grandi)
- associa immagini (se presenti nella cartella `images/`)

Note:
- Lo script è scritto per PostgreSQL (usa `psycopg2` e comandi come `COPY`). Se vuoi usare SQLite modifica lo script o carica i CSV con un tool diverso.
- In caso di errori, i log indicano il comando SQL che ha fallito (preview troncata) per facilitare il debug.

## Eseguire la web app (Streamlit)

Per avviare l'interfaccia Streamlit usa il seguente comando dalla root del progetto:

```bash
streamlit run streamlit/Login.py
```

Pagine principali:
- Login: identificazione/registrazione utente (salva in `users`).
- Gestione Ingredienti: seleziona gli ingredienti che l'utente possiede; la tabella `user_owned_ingredients` viene aggiornata.
- In Cerca di Ispirazione: seleziona categoria e ottieni ricette ordinate per percentuale di ingredienti posseduti; il ranking viene ricalcolato combinando owned_ratio e similarità con ricette preferite.
- Le tue ricette preferite: mostra le ricette salvate dall'utente e permette di esplorare ricette simili.


## Motore di raccomandazione — come funziona

- Costruzione del corpus: per ogni ricetta si crea un testo unendo titolo, categoria e lista di ingredienti (vedi `build_recipe_corpus`).
- TF‑IDF: `TfidfVectorizer` (unigram+bigram) viene usato per trasformare il corpus in vettori.
- Similarità: `cosine_similarity` calcola la matrice NxN tra ricette.
- Ranking ibrido: per una categoria, si prendono le top-N ricette ordinate per owned_ratio (quanti ingredienti l'utente possiede). Poi si ricalcola il punteggio finale combinando owned_ratio (weight ~0.7) e similarità media rispetto alle ricette preferite dell'utente (weight ~0.3).

Script utili:
- `streamlit/recommendation/similarity/compute_item_similarity.py` — script standalone che costruisce il corpus e stampa la matrice di similarità e le top-k simili per ogni ricetta.

## Dati e licenze

- Il dataset delle ricette è incluso nella cartella `data/processed/italian gastronomic recipes dataset/` e riporta una licenza (nel readme del dataset): Creative Commons Attribution 4.0 (vedi `data/processed/.../readme.md`). Se utilizzi i dati per pubblicazioni o demo, cita la fonte come indicato.

## Troubleshooting rapido

- Errore: CSV mancanti -> assicurati che i file siano in `data/processed/italian gastronomic recipes dataset/foods/CSV/` e che i separatori siano `;` come atteso dallo script.
- Errore: connessione PostgreSQL -> verifica `PG*` env vars, utente/permessi e che il server PostgreSQL sia in ascolto sulla porta configurata.
- Errore: moduli mancanti -> esegui `pip install -r requirements.txt` in un virtualenv pulito.
- Streamlit non trova la pagina -> lancia `streamlit run streamlit/Login.py` dalla root del progetto.

