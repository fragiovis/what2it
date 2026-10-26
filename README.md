# 🍝 What2It — Smart Fridge Recipe Recommender

*"What can I cook with what I have?"* What2It recommends Italian recipes based on the ingredients in your fridge and on the recipes you have liked before.

*Course project · Università degli Studi Roma Tre (2025) · Francesco Giovanardi, Alessandro Cavina*

📄 Report (Italian): [`relazione.pdf`](relazione.pdf) · Slides: [`presentazione.pdf`](presentazione.pdf)

## Features
- **Account and pantry**: sign up / log in, then select the ingredients you own.
- **Find inspiration**: pick a category and get recipes ranked by a hybrid score.
- **Favourites**: save recipes and explore the ones most similar to them.

## How the recommender works
1. **Corpus**: each recipe becomes a text made of its title, category and ingredient list.
2. **TF-IDF** (`TfidfVectorizer`, unigrams + bigrams) turns the corpus into vectors.
3. **Cosine similarity** gives the recipe-to-recipe similarity matrix.
4. **Hybrid ranking**: within a category, the top-N recipes by **owned ratio** (share of ingredients the user has) are re-scored as

   `final_score = 0.7 · owned_ratio + 0.3 · mean similarity to the user's favourite recipes`

   so the system combines content-based filtering with what the user can actually cook today.

## Tech stack
Python · Streamlit (multi-page app) · PostgreSQL (`psycopg2`, `COPY` bulk import) · scikit-learn · pandas · NumPy

## Project structure
```text
what2it/
├── data/processed/italian gastronomic recipes dataset/   # recipes, ingredients, classes (CSV)
├── database/
│   ├── database_setup.sql        # schema
│   └── populate_database.py      # creates the DB, applies the schema, bulk-loads the CSVs, links images
├── images/                       # recipe images
├── streamlit/
│   ├── Login.py                  # entry point: login / registration
│   ├── pages/
│   │   ├── Gestione_Ingredienti.py        # manage your ingredients
│   │   ├── In_Cerca_Di_Ispirazione.py     # recommendations
│   │   └── Le_Tue_Ricette_Preferite.py    # favourites and similar recipes
│   └── recommendation/
│       └── compute_item_similarity.py     # standalone TF-IDF similarity script
├── start-all.sh                  # creates/populates the DB and starts the app
└── start-streamlit.sh            # starts only the app
```

## Getting started
Requirements: Python 3.10+ and a running PostgreSQL server.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with the database connection:
```bash
PGUSER=user
PGPASSWORD=password
PGDATABASE=db_name
PGHOST=localhost
PGPORT=5432
```

First run (creates and populates the database, then starts the web app):
```bash
chmod +x start-all.sh && ./start-all.sh
```
Later runs, with the database already in place:
```bash
./start-streamlit.sh        # or: streamlit run streamlit/Login.py
```

`populate_database.py` checks that the CSVs exist, creates the database if needed, applies `database_setup.sql`, imports the CSVs with `COPY` and links the images in `images/`.

## Data
The recipes come from the *Italian gastronomic recipes* dataset included in `data/processed/`, released under Creative Commons Attribution 4.0. Please credit the source if you reuse it.

## Troubleshooting
- **Missing CSVs**: make sure they are in `data/processed/italian gastronomic recipes dataset/foods/CSV/` and use `;` as separator.
- **PostgreSQL connection errors**: check the `PG*` variables, user permissions and that the server listens on the configured port.
- **Missing modules**: run `pip install -r requirements.txt` in a clean virtual environment.
- **Streamlit cannot find the pages**: launch `streamlit run streamlit/Login.py` from the project root.
