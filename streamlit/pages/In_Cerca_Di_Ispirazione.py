import os
from typing import Dict, List, Tuple

import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor
from recommendation.compute_item_similarity import (
    build_recipe_corpus,
    compute_similarity_matrix,
)

# Config DB dalla sessione o variabili d'ambiente
DB_CONFIG = st.session_state.get(
    "DB_CONFIG",
    {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "database": os.getenv("PGDATABASE", "italian_recipes"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", "postgres"),
    },
)


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# Funzioni per similarità (riuso della logica del tuo script)
def fetch_recipes_and_ingredients_for_similarity() -> Tuple[List[Dict], Dict[int, List[str]]]:
    """Replica fetch_recipes_and_ingredients usando la stessa connessione DB della pagina."""
    with get_conn() as conn, conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(
            """
            SELECT recipe_id, recipe_name, category_name
            FROM recipes
            ORDER BY recipe_id
            """
        )
        recipes = cur.fetchall()

        cur.execute(
            """
            SELECT ri.recipe_id, i.ingredient_name
            FROM recipe_ingredients ri
            JOIN ingredients i ON i.ingredient_id = ri.ingredient_id
            ORDER BY ri.recipe_id
            """
        )
        rows = cur.fetchall()

    ing_by_recipe: Dict[int, List[str]] = {}
    for r in rows:
        rid = int(r["recipe_id"])  # DictCursor fornisce accesso per chiave
        name = str(r["ingredient_name"]) if r["ingredient_name"] is not None else ""
        if rid not in ing_by_recipe:
            ing_by_recipe[rid] = []
        if name:
            ing_by_recipe[rid].append(name)

    return recipes, ing_by_recipe


@st.cache_resource(show_spinner=False)
def get_similarity_resources():
    """Calcola e cache la matrice di similarità e la mappa recipe_id->indice."""
    recipes, ing_by_recipe = fetch_recipes_and_ingredients_for_similarity()
    """Recipes contiene le ricette con il rispettivo id, ing_by_recipe è un dizionario che a ogni recipe_id associa il nome dell'ingrediente"""
    corpus, index_to_recipe = build_recipe_corpus(recipes, ing_by_recipe)
    """Corpus è una lista di stringhe (una per ricetta), index_to_recipe è una lista di tuple (recipe_id, recipe_name) nello stesso ordine del corpus"""
    sim = compute_similarity_matrix(corpus)
    """
    Usa TF-IDF per creare embedding testuali e calcola la cosine similarity NxN.
    """
    rid_to_idx = {rid: i for i, (rid, _name) in enumerate(index_to_recipe)}
    return sim, rid_to_idx
 

def fetch_user_favorites(user_id: int) -> List[int]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT recipe_id
            FROM user_selected_recipes
            WHERE user_id = %s
            """,
            (user_id,),
        )
        return [row[0] for row in cur.fetchall()]


def fetch_categories() -> List[str]:
    """Recupera le categorie disponibili dal DB, normalizzando eventuali spazi."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT TRIM(category_name) AS category_name
            FROM recipes
            WHERE category_name IS NOT NULL AND TRIM(category_name) <> ''
            ORDER BY 1
            """
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]


def fetch_top_recipes_by_owned_ratio(
    user_id: int, category_name: str, limit: int = 10
) -> List[Dict]:
    """Restituisce le top ricette per categoria, ordinate per percentuale di ingredienti posseduti dall'utente."""
    sql = """
     SELECT r.recipe_id,
         r.recipe_name,
         r.recipe_link,
         r.category_name,
         r.cost,
         r.difficulty,
         r.preparation_time,
         r.image_path,
         COALESCE(SUM(CASE WHEN uoi.user_id IS NOT NULL THEN 1 ELSE 0 END), 0) AS owned_count,
         COUNT(ri.ingredient_id) AS total_count,
         COALESCE(SUM(CASE WHEN uoi.user_id IS NOT NULL THEN 1 ELSE 0 END), 0)::float
           / NULLIF(COUNT(ri.ingredient_id), 0) AS owned_ratio
     FROM recipes r
     JOIN recipe_ingredients ri ON ri.recipe_id = r.recipe_id
     LEFT JOIN user_owned_ingredients uoi
         ON uoi.ingredient_id = ri.ingredient_id AND uoi.user_id = %s
     WHERE LOWER(TRIM(r.category_name)) = LOWER(TRIM(%s))
     GROUP BY r.recipe_id, r.recipe_name, r.recipe_link, r.category_name, r.cost, r.difficulty, r.preparation_time, r.image_path
     ORDER BY owned_ratio DESC NULLS LAST, total_count DESC, r.recipe_name ASC
     LIMIT %s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (user_id, category_name, limit))
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in rows]


def add_favorite(user_id: int, recipe_id: int) -> None:
    """Aggiunge la ricetta ai preferiti dell'utente."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_selected_recipes (user_id, recipe_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, recipe_id) DO NOTHING
            """,
            (user_id, recipe_id),
        )
        conn.commit()


def remove_favorite(user_id: int, recipe_id: int) -> None:
    """Rimuove la ricetta dai preferiti dell'utente."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM user_selected_recipes WHERE user_id = %s AND recipe_id = %s",
            (user_id, recipe_id),
        )
        conn.commit()

# Configurazione pagina e larghezza contenitore (per allargare le card)
st.set_page_config(page_title="In Cerca Di Ispirazione", page_icon="💡", layout="wide")
st.markdown(
    """
    <style>
    .block-container { max-width: 1400px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("💡 In Cerca di Ispirazione")

# Verifica login
if "user" not in st.session_state or not st.session_state["user"]:
    st.warning("Devi essere loggato per ricevere suggerimenti di ricette.")
    try:
        if st.button("Vai al Login"):
            st.switch_page("Login.py")
    except Exception:
        st.info("Apri manualmente la pagina di Login.")
    st.stop()

user = st.session_state["user"]
st.caption(f"Utente: {user['nickname']}")

# Selettore categorie con pulsanti orizzontali (dinamico da DB)
try:
    CATEGORIES = fetch_categories()
except Exception as e:
    st.error(f"Errore nel caricamento delle categorie: {e}")
    CATEGORIES = []

if not CATEGORIES:
    st.info("Nessuna categoria trovata nel database.")
    st.stop()

if (
    "insp_selected_category" not in st.session_state
    or st.session_state["insp_selected_category"] not in CATEGORIES
):
    st.session_state["insp_selected_category"] = CATEGORIES[0]

st.write("Seleziona una categoria per vedere le ricette che puoi preparare con gli ingredienti che possiedi:")
cols = st.columns(len(CATEGORIES))
for i, cat in enumerate(CATEGORIES):
    is_selected = st.session_state["insp_selected_category"].lower() == cat.lower()
    btn_type = "primary" if is_selected else "secondary"
    with cols[i]:
        if st.button(cat, key=f"insp_cat_{cat}", use_container_width=True, type=btn_type):
            st.session_state["insp_selected_category"] = cat
            st.rerun()

selected_category = st.session_state["insp_selected_category"]
st.subheader(f"Categoria: {selected_category}")

# Carica top 10 ricette per percentuale di ingredienti posseduti e ricalcola ranking con similarity
try:
    recommendations = fetch_top_recipes_by_owned_ratio(
        user_id=user["user_id"], category_name=selected_category, limit=10
    )

    # Risorse di similarità e preferiti utente
    sim, rid_to_idx = get_similarity_resources()
    fav_ids = fetch_user_favorites(user_id=user["user_id"]) or []

    def user_similarity_for_recipe(rid: int) -> float:
        if not fav_ids:
            return 0.0
        idx_r = rid_to_idx.get(rid)
        if idx_r is None:
            return 0.0
        sims = []
        for fid in fav_ids:
            idx_f = rid_to_idx.get(fid)
            if idx_f is not None:
                sims.append(float(sim[idx_r][idx_f]))
        return float(sum(sims) / len(sims)) if sims else 0.0

    # Calcola punteggio finale e riordina
    for rec in recommendations:
        ratio = float(rec.get("owned_ratio") or 0.0)
        sim_avg = user_similarity_for_recipe(int(rec["recipe_id"]))
        rec["final_score"] = 0.7 * ratio + 0.3 * sim_avg

    recommendations.sort(key=lambda r: r.get("final_score", 0.0), reverse=True) # Ordina per punteggio finale
except Exception as e:
    st.error(f"Errore nel calcolo delle raccomandazioni: {e}")
    recommendations = []

if not recommendations:
    st.info("Nessuna ricetta trovata per la categoria scelta.")
else:
    import pathlib
    for rec in recommendations:
        name = rec.get("recipe_name") or f"Ricetta #{rec.get('recipe_id')}"
        link = rec.get("recipe_link")
        cat = rec.get("category_name")
        cost = rec.get("cost")
        diff = rec.get("difficulty")
        prep = rec.get("preparation_time")
        owned = rec.get("owned_count") or 0
        total = rec.get("total_count") or 0
        ratio = rec.get("owned_ratio") or 0.0
        percent = int(round(ratio * 100)) if total else 0
        image_path = rec.get("image_path")

        # Costruisci il percorso assoluto rispetto alla root del progetto
        if image_path:
            abs_image_path = str(pathlib.Path(__file__).parent.parent.parent / image_path)
        else:
            abs_image_path = None

        with st.container(border=True):
            cols = st.columns([2, 7, 2], vertical_alignment="center")
            with cols[0]:
                if abs_image_path and os.path.exists(abs_image_path):
                    st.image(abs_image_path, width='stretch')
            with cols[1]:
                if link:
                    st.markdown(f"**[{name}]({link})**")
                else:
                    st.markdown(f"**{name}**")

                meta_parts = []
                if cat:
                    meta_parts.append(f"Categoria: {cat}")
                if cost is not None:
                    meta_parts.append(f"Costo: {cost}")
                if diff is not None:
                    meta_parts.append(f"Difficoltà: {diff}")
                if prep is not None:
                    meta_parts.append(f"Tempo prep: {prep} min")
                meta_parts.append(f"Ingredienti posseduti: {owned}/{total} ({percent}%)")
                # Mostra anche il punteggio finale calcolato (0..1)
                score = rec.get("final_score")
                if score is not None:
                    try:
                        meta_parts.append(f"Punteggio: {score:.2f}")
                    except Exception:
                        # in caso di tipo non numerico
                        meta_parts.append(f"Punteggio: {score}")
                st.caption(" • ".join(meta_parts))


            with cols[2]:
                # Pulsante Salva con stato verde quando la ricetta è nei preferiti
                rid = rec["recipe_id"]
                is_saved = rid in (fav_ids or [])
                wrapper_id = f"savebox-{rid}"
                st.markdown(f'<div id="{wrapper_id}">', unsafe_allow_html=True)
                # Allarga leggermente il pulsante "Salva/Salvato" con una min-width e più padding
                st.markdown(
                    f"""
                    <style>
                    #{wrapper_id} button {{
                        min-width: 120px !important;          /* rende il tasto un po' più largo */
                        padding-left: 16px !important;         /* aumenta padding orizzontale */
                        padding-right: 16px !important;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                if is_saved:
                    st.markdown(
                        f"""
                        <style>
                        /* Colora di verde SOLO il pulsante di questo wrapper quando salvata */
                        #{wrapper_id} button {{
                            background-color: #22c55e !important; /* green-500 */
                            border-color: #16a34a !important;      /* green-600 */
                            color: #ffffff !important;
                        }}
                        #{wrapper_id} button:hover {{
                            background-color: #16a34a !important; /* green-600 */
                            border-color: #15803d !important;      /* green-700 */
                            color: #ffffff !important;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                btn_label = "Salvato" if is_saved else "Salva"
                btn_help = "Rimuovi dai preferiti" if is_saved else "Aggiungi ai preferiti"
                if st.button(btn_label, key=f"insp_save_{rid}", use_container_width=True, help=btn_help):
                    try:
                        if is_saved:
                            remove_favorite(user_id=user["user_id"], recipe_id=rid)
                            st.toast("Rimossa dai preferiti", icon="✅")
                        else:
                            add_favorite(user_id=user["user_id"], recipe_id=rid)
                            st.toast("Aggiunta ai preferiti", icon="✅")
                        try:
                            st.rerun()
                        except Exception:
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Errore nel salvataggio: {e}")
                st.markdown("</div>", unsafe_allow_html=True)
