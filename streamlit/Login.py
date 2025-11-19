import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional
import streamlit as st

# Optional TOML parser (Python 3.11+)
try:
    import tomllib  # type: ignore[attr-defined]
except Exception:
    tomllib = None
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Tuple

from dotenv import load_dotenv

# Cerca .env nella root del progetto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
# --------------- Utility DB ---------------

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def get_user_by_nickname(nickname: str) -> Dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, name, surname, nickname FROM users WHERE nickname = %s",
            (nickname,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"user_id": row[0], "name": row[1], "surname": row[2], "nickname": row[3]}

def create_user(name: str, surname: str, nickname: str) -> Dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (name, surname, nickname) VALUES (%s, %s, %s) RETURNING user_id",
            (name, surname, nickname)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return {"user_id": user_id, "name": name, "surname": surname, "nickname": nickname}

@st.cache_data(show_spinner=False)
def get_all_ingredients() -> List[Tuple[int, str]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT ingredient_id, ingredient_name FROM ingredients ORDER BY ingredient_name"
        )
        return cur.fetchall()  # List[(id, name)]

def get_user_owned(user_id: int) -> List[int]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT ingredient_id FROM user_owned_ingredients WHERE user_id = %s",
            (user_id,)
        )
        return [r[0] for r in cur.fetchall()]

def sync_user_owned(user_id: int, selected_ids: List[int]) -> None:
    """
    Porta user_owned_ingredients esattamente a selected_ids:
    - Inserisce quelli mancanti
    - Rimuove quelli non più presenti
    """
    with get_conn() as conn, conn.cursor() as cur:
        # Recupera attuali
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
            # ON CONFLICT DO NOTHING perché PK (user_id, ingredient_id)
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
            # Costruisce DELETE con IN dinamico
            placeholders = ",".join(["%s"] * len(to_delete))
            cur.execute(
                f"""
                DELETE FROM user_owned_ingredients
                WHERE user_id = %s AND ingredient_id IN ({placeholders})
                """,
                (user_id, *to_delete)
            )

        conn.commit()

# --------------- UI ---------------

PAGE_CONFIG_CACHE_KEY = "page_config_toml"

def load_page_config() -> Dict:
    """Legge src/ui/web/page.toml se presente, altrimenti ritorna defaults."""
    default = {"post_registration_page": "pages/gestione_ingredienti.py"}
    path = os.path.join(os.path.dirname(__file__), "page.toml")
    try:
        if tomllib is None:
            return default
        with open(path, "rb") as f:
            data = tomllib.load(f)
        # si aspetta una chiave [navigation] con post_registration_page
        nav = data.get("navigation", {}) if isinstance(data, dict) else {}
        page = nav.get("post_registration_page") if isinstance(nav, dict) else None
        if isinstance(page, str) and page.strip():
            default["post_registration_page"] = page.strip()
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return default

st.set_page_config(page_title="Identificazione Utente", page_icon="🧊", layout="centered")

# Redirect automatico se già loggato
if "user" in st.session_state and st.session_state["user"]:
    st.switch_page("pages/Gestione_Ingredienti.py")
    st.stop()

st.subheader("1) Identificazione utente")
nickname = st.text_input("Nickname (username)")

user = None
if st.button("Continua"):
    if not nickname:
        st.error("Inserisci un nickname.")
    else:
        try:
            user = get_user_by_nickname(nickname.strip())
            if user:
                st.session_state["user"] = user
                st.success(f"Benvenuto {user['name']} {user['surname']} (ID: {user['user_id']})")
                st.switch_page("pages/Gestione_Ingredienti.py")
            else:
                st.info("Utente non trovato. Compila il form di registrazione qui sotto.")
                st.session_state["pending_registration_nickname"] = nickname.strip()
        except Exception as e:
            st.error(f"Errore durante la ricerca utente: {e}")

# Registrazione
if "user" not in st.session_state:
    st.subheader("2) Registrazione (se non sei già registrato)")
    with st.form("registration_form", clear_on_submit=False):
        name = st.text_input("Nome")
        surname = st.text_input("Cognome")
        reg_nickname = st.text_input(
            "Nickname",
            value=st.session_state.get("pending_registration_nickname", "")
        )
        submitted = st.form_submit_button("Registrati")
        if submitted:
            if not (name and surname and reg_nickname):
                st.error("Compila tutti i campi richiesti (name, surname, nickname).")
            else:
                try:
                    user = create_user(name.strip(), surname.strip(), reg_nickname.strip())
                    st.session_state["user"] = user
                    st.success(f"Registrazione completata! ID utente: {user['user_id']}")
                    st.switch_page("pages/Gestione_Ingredienti.py")
                except psycopg2.errors.UniqueViolation:
                    st.error("Questo nickname è già in uso. Scegline un altro.")
                except Exception as e:
                    st.error(f"Errore durante la registrazione: {e}")


st.caption("Nota: il database non viene modificato nello schema; vengono aggiornate solo le righe in users e user_owned_ingredients.")