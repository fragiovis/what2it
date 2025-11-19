import os
import sys
import logging
from typing import List, Dict, Tuple
import streamlit as st
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
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

@st.cache_data(show_spinner=False)
def get_all_ingredients() -> List[Tuple[int, str]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT ingredient_id, ingredient_name FROM ingredients ORDER BY ingredient_name"
        )
        return cur.fetchall()

def get_user_owned(user_id: int) -> List[int]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT ingredient_id FROM user_owned_ingredients WHERE user_id = %s",
            (user_id,)
        )
        return [r[0] for r in cur.fetchall()]

def sync_user_owned(user_id: int, selected_ids: List[int]) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT ingredient_id FROM user_owned_ingredients WHERE user_id = %s",
            (user_id,)
        )
        current_ids = {r[0] for r in cur.fetchall()}
        target_ids = set(selected_ids)

        to_insert = list(target_ids - current_ids)
        to_delete = list(current_ids - target_ids)

        if to_insert:
            rows = [(user_id, ing_id) for ing_id in to_insert]
            execute_values(
                cur,
                """
                INSERT INTO user_owned_ingredients (user_id, ingredient_id)
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                rows
            )

        if to_delete:
            placeholders = ",".join(["%s"] * len(to_delete))
            cur.execute(
                f"""
                DELETE FROM user_owned_ingredients
                WHERE user_id = %s AND ingredient_id IN ({placeholders})
                """,
                (user_id, *to_delete)
            )

        conn.commit()

# Configurazione pagina e larghezza contenitore
st.set_page_config(page_title="Gestione Ingredienti", page_icon="🧊", layout="wide")
st.markdown(
    """
    <style>
    .block-container { max-width: 1400px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("🧊 Gestione Ingredienti")

# Verifica utente in sessione
if "user" not in st.session_state:
    st.warning("Nessun utente in sessione. Torna alla pagina di login/registrazione.")
    try:
        if st.button("Vai al login/registrazione"):
            # path relativo alla cartella streamlit
            st.switch_page("streamlit_app.py")
    except Exception:
        st.info("Apri manualmente: streamlit_app.py")
    st.stop()

user = st.session_state["user"]
st.caption(f"Utente: {user['nickname']}")

st.subheader("Seleziona gli ingredienti che hai in frigo")
try:
    ingredients = get_all_ingredients()
    ing_options = {name: ing_id for (ing_id, name) in ingredients}
    owned_ids = set(get_user_owned(user["user_id"]))
    default_names = [name for (ing_id, name) in ingredients if ing_id in owned_ids]

    selected_names = st.multiselect(
        "Ingredienti",
        options=list(ing_options.keys()),
        default=default_names
    )

    if st.button("Salva ingredienti"):
        selected_ids = [ing_options[name] for name in selected_names]
        sync_user_owned(user["user_id"], selected_ids)
        st.success("Ingredienti aggiornati correttamente!")
except Exception as e:
    st.error(f"Errore durante il caricamento/aggiornamento degli ingredienti: {e}")
