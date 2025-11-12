import os
from typing import Dict, List, Tuple
import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor
from recommendation.similarity.compute_item_similarity import (
    build_recipe_corpus,
    compute_similarity_matrix,
)
import pathlib

# DB config dalla sessione o variabili d'ambiente
DB_CONFIG = st.session_state.get("DB_CONFIG", {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "database": os.getenv("PGDATABASE", "italian_recipes"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
})

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@st.cache_resource(show_spinner=False)
def get_similarity_resources():
    """Carica ricette/ingredienti, costruisce il corpus e calcola la matrice di similarità.
    Ritorna anche mappe di supporto: recipe_id -> indice e recipe_id -> link.
    """
    with get_conn() as conn, conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(
            """
            SELECT recipe_id, recipe_name, category_name, recipe_link
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
    rid_to_link: Dict[int, str] = {}
    for rec in recipes:
        rid = int(rec["recipe_id"])
        rid_to_link[rid] = rec.get("recipe_link") or ""
    for r in rows:
        rid = int(r["recipe_id"])
        name = str(r["ingredient_name"]) if r["ingredient_name"] is not None else ""
        if rid not in ing_by_recipe:
            ing_by_recipe[rid] = []
        if name:
            ing_by_recipe[rid].append(name)
    corpus, index_to_recipe = build_recipe_corpus(recipes, ing_by_recipe)
    sim = compute_similarity_matrix(corpus)
    rid_to_idx = {rid: i for i, (rid, _name) in enumerate(index_to_recipe)}
    return sim, rid_to_idx, index_to_recipe, rid_to_link

def fetch_favorites(user_id: int) -> List[Dict]:
    """Ritorna le ricette preferite dell'utente con info ricetta, ordinate per data di selezione."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.recipe_id, r.recipe_name, r.recipe_link, r.category_name,
                   r.cost, r.difficulty, r.preparation_time, r.image_path,
                   usr.selected_at
            FROM user_selected_recipes AS usr
            JOIN recipes AS r ON r.recipe_id = usr.recipe_id
            WHERE usr.user_id = %s
            ORDER BY usr.selected_at DESC
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in rows]

def remove_favorite(user_id: int, recipe_id: int) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM user_selected_recipes WHERE user_id = %s AND recipe_id = %s",
            (user_id, recipe_id)
        )
        conn.commit()

def add_favorite(user_id: int, recipe_id: int) -> None:
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

# Configurazione pagina e larghezza contenitore
st.set_page_config(page_title="Le tue ricette preferite", page_icon="❤️", layout="wide")
st.markdown(
    """
    <style>
    .block-container { max-width: 1400px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("❤️ Le tue ricette preferite")

# Verifica login
if "user" not in st.session_state or not st.session_state["user"]:
    st.warning("Devi essere loggato per vedere le tue ricette preferite.")
    try:
        if st.button("Vai al Login"):
            st.switch_page("Login.py")
    except Exception:
        st.info("Apri manualmente la pagina di Login.")
    st.stop()

user = st.session_state["user"]
st.caption(f"Utente: {user['nickname']}")

# Carica preferiti
try:
    favorites = fetch_favorites(user_id=user["user_id"])
except Exception as e:
    st.error(f"Errore durante il caricamento dei preferiti: {e}")
    favorites = []

if not favorites:
    st.info("Non hai ancora aggiunto ricette ai preferiti.")
else:
    # Risorse similarità con mappe
    sim, rid_to_idx, index_to_recipe, rid_to_link = get_similarity_resources()
    for rec in favorites:
        name = rec.get("recipe_name") or f"Ricetta #{rec.get('recipe_id')}"
        link = rec.get("recipe_link")
        cat = rec.get("category_name")
        cost = rec.get("cost")
        diff = rec.get("difficulty")
        prep = rec.get("preparation_time")
        image_path = rec.get("image_path")

        # Costruisci il percorso assoluto rispetto alla root del progetto
        if image_path:
            abs_image_path = str(pathlib.Path(__file__).parent.parent.parent / image_path)
        else:
            abs_image_path = None

        with st.container(border=True):
            cols = st.columns([2, 6, 1], vertical_alignment="center")
            with cols[0]:
                if abs_image_path and os.path.exists(abs_image_path):
                    st.image(abs_image_path, width='stretch')
            with cols[1]:
                # Titolo e link
                if link:
                    st.markdown(f"**[{name}]({link})**")
                else:
                    st.markdown(f"**{name}**")

                # Metadati
                meta_parts = []
                if cat:
                    meta_parts.append(f"Categoria: {cat}")
                if cost is not None:
                    meta_parts.append(f"Costo: {cost}")
                if diff is not None:
                    meta_parts.append(f"Difficoltà: {diff}")
                if prep is not None:
                    meta_parts.append(f"Tempo prep: {prep} min")
                if meta_parts:
                    st.caption(" • ".join(meta_parts))

            with cols[1]:
                # Pulsante Salva verde (toggle)
                rid = rec["recipe_id"]
                wrapper_id = f"favsave-{rid}"
                st.markdown(f'<div id="{wrapper_id}">', unsafe_allow_html=True)
                # Ricetta è nei preferiti -> bottone verde e testo "Salvato"
                st.markdown(
                    f"""
                    <style>
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
                # Card preferiti: aumento larghezza colonna del bottone e impedisco a capo
                st.markdown(
                    f"""
                    <style>
                    #favbox-{rid} button {{
                        min-width: 140px !important;
                        white-space: nowrap !important;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Salvato", key=f"fav_save_{rid}", use_container_width=True, help="Rimuovi dai preferiti"):
                    try:
                        remove_favorite(user_id=user["user_id"], recipe_id=rid)
                        st.toast("Rimossa dai preferiti", icon="✅")
                        try:
                            st.rerun()
                        except Exception:
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Errore nella rimozione: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

                # Pulsante "Vorrei qualcosa di simile" con toggle mostra/nascondi
                sim_key = f"show_sim_{rid}"
                if sim_key not in st.session_state:
                    st.session_state[sim_key] = False
                if st.button("Vorrei qualcosa di simile", key=f"fav_sim_{rid}", use_container_width=True):
                    st.session_state[sim_key] = not st.session_state.get(sim_key, False)
                # Se attivo, mostra top3 simili con link
                if st.session_state.get(sim_key, False):
                    try:
                        idx = rid_to_idx.get(rid)
                        if idx is None:
                            st.warning("Impossibile calcolare similarità per questa ricetta.")
                        else:
                            scores = [(j, float(sim[idx][j])) for j in range(len(index_to_recipe)) if j != idx]
                            scores.sort(key=lambda x: x[1], reverse=True)
                            top3 = scores[:3]
                            st.caption("Ricette simili:")
                            for j, s in top3:
                                rid_j, name_j = index_to_recipe[j]
                                link_j = rid_to_link.get(rid_j)
                                if link_j:
                                    st.markdown(f"- [{name_j}]({link_j}) (sim: {s:.2f})")
                                else:
                                    st.markdown(f"- {name_j} (sim: {s:.2f})")
                    except Exception as e:
                        st.error(f"Errore nel calcolo delle simili: {e}")

# Nota: la pagina è interattiva; dopo il click il dataset si aggiorna e la page viene ricaricata.