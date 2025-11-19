import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import DictCursor
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


from dotenv import load_dotenv

# Cerca .env nella root del progetto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
env_path = PROJECT_ROOT / ".env"

if not env_path.exists():
    print(f"❌ ERRORE: file .env mancante! Crea {env_path}")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration (leggi user/password da env; non usare valori hardcoded sensibili)
DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "database": os.getenv("PGDATABASE", "italian_recipes"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "port": int(os.getenv("PGPORT", "5432")),
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def fetch_recipes_and_ingredients() -> Tuple[List[Dict], Dict[int, List[str]]]:
    """
    Ritorna:
      - lista ricette con campi: recipe_id, recipe_name, category_name (se presente)
      - dizionario recipe_id -> lista di ingredienti (nomi)
    """
    with get_conn() as conn, conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            SELECT recipe_id, recipe_name, category_name
            FROM recipes
            ORDER BY recipe_id
        """)
        recipes = cur.fetchall()

        cur.execute("""
            SELECT ri.recipe_id, i.ingredient_name
            FROM recipe_ingredients ri
            JOIN ingredients i ON i.ingredient_id = ri.ingredient_id
            ORDER BY ri.recipe_id
        """)
        rows = cur.fetchall()

    ing_by_recipe: Dict[int, List[str]] = {}
    for r in rows:
        rid = int(r["recipe_id"])
        name = str(r["ingredient_name"]) if r["ingredient_name"] is not None else ""
        if rid not in ing_by_recipe:
            ing_by_recipe[rid] = []
        if name:
            ing_by_recipe[rid].append(name)

    return recipes, ing_by_recipe


def build_recipe_corpus(recipes: List[Dict], ing_by_recipe: Dict[int, List[str]]) -> Tuple[List[str], List[Tuple[int, str]]]:
    """
    Costruisce un testo per ricetta (embedding di contenuto):
      testo = recipe_name + category_name + ingredienti concatenati
    Ritorna:
      - corpus: lista di stringhe (una per ricetta)
      - index_to_recipe: lista di tuple (recipe_id, recipe_name) nello stesso ordine del corpus
    """
    corpus = []
    index_to_recipe: List[Tuple[int, str]] = []

    for row in recipes:
        rid = int(row["recipe_id"])
        title = str(row["recipe_name"]) if row["recipe_name"] is not None else ""
        category = str(row["category_name"]) if row["category_name"] is not None else ""
        ingredients = " ".join(ing_by_recipe.get(rid, []))
        text = " ".join([title, category, ingredients]).strip()
        corpus.append(text if text else title)
        index_to_recipe.append((rid, title))

    return corpus, index_to_recipe


def compute_similarity_matrix(corpus: List[str]) -> np.ndarray:
    """
    Usa TF-IDF per creare embedding testuali e calcola la cosine similarity NxN.
    """
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words=None,       
        max_features=None,      
        ngram_range=(1, 2),     
    )
    X = vectorizer.fit_transform(corpus)   
    sim = cosine_similarity(X)            
    return sim


def print_matrix_and_summary(sim: np.ndarray, index_to_recipe: List[Tuple[int, str]], top_k: int = 5) -> None:
    """
    Stampa:
      - mapping indice -> (recipe_id, recipe_name)
      - dimensione matrice
      - matrice (troncata se troppo grande)
      - top_k ricette più simili per ogni ricetta (escludendo self)
    """
    n = sim.shape[0]
    print("=== Recipe Index Mapping ===")
    for i, (rid, title) in enumerate(index_to_recipe):
        print(f"[{i}] id={rid} name={title}")

    print("\n=== Similarity Matrix ===")
    print(f"Shape: {sim.shape} (NxN, N=numero ricette)")

    # Se N è grande, stampiamo una versione compatta
    if n <= 30:
        # stampa completa con 3 decimali
        np.set_printoptions(precision=3, suppress=True)
        print(sim)
    else:
        # stampa righe di esempio
        np.set_printoptions(precision=3, suppress=True)
        print("(Matrice troppo grande, stampo le prime 10 righe e ultime 10)")
        head = sim[:10, :10]
        tail = sim[-10:, -10:]
        print("Top-left 10x10:")
        print(head)
        print("\nBottom-right 10x10:")
        print(tail)

    print("\n=== Top similar recipes (per riga) ===")
    for i in range(n):
        # escludi self (i)
        scores = [(j, sim[i, j]) for j in range(n) if j != i]
        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:top_k]
        i_id, i_name = index_to_recipe[i]
        print(f"\nRicetta [{i}] id={i_id} name={i_name}")
        for j, s in top:
            j_id, j_name = index_to_recipe[j]
            print(f"  -> sim={s:.3f} con [{j}] id={j_id} name={j_name}")


def main():
    try:
        recipes, ing_by_recipe = fetch_recipes_and_ingredients()
        if not recipes:
            print("Nessuna ricetta trovata nel database.")
            sys.exit(0)

        corpus, index_to_recipe = build_recipe_corpus(recipes, ing_by_recipe)
        sim = compute_similarity_matrix(corpus)
        print_matrix_and_summary(sim, index_to_recipe, top_k=5)
    except Exception as e:
        print(f"Errore durante il calcolo della similarità: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()