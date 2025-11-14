#!/usr/bin/env python3
"""
PostgreSQL Database Population Script for Italian Recipe Management System
This script executes the database setup and populates it with data from translated CSV files.
"""

import psycopg2
import os
import sys
import logging
from pathlib import Path
import csv
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'italian_recipes',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to postgres database to create the target database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("""
            SELECT 1 FROM pg_database WHERE datname = %s
        """, (DB_CONFIG['database'],))
        
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            logger.info(f"Database '{DB_CONFIG['database']}' created successfully")
        else:
            logger.info(f"Database '{DB_CONFIG['database']}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

def execute_sql_script(script_path):
    """Execute SQL script file."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Rimuovi commenti di tipo /* ... */ (anche multi-linea)
        while '/*' in sql_content:
            start = sql_content.find('/*')
            end = sql_content.find('*/', start + 2)
            if end == -1:
                # Commento non chiuso: tronca dal '/*' in poi
                sql_content = sql_content[:start]
                break
            sql_content = sql_content[:start] + sql_content[end+2:]

        # Rimuovi commenti di riga che iniziano con --
        lines = []
        for line in sql_content.splitlines():
            stripped = line.strip()
            if stripped.startswith('--'):
                continue
            lines.append(line)
        sql_content = '\n'.join(lines)
        
        # Esegui in modo sicuro più statement separati da ';'
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                conn.rollback()
                preview = ' '.join(stmt.split())
                logger.error(f"Statement fallito: {preview[:200]}...")
                logger.error(f"Dettagli errore: {e}")
                cursor.close()
                conn.close()
                return False
        conn.commit()

        cursor.close()
        conn.close()
        
        logger.info("SQL script eseguito correttamente (schema creato)")
        return True
        
    except Exception as e:
        logger.error(f"Errore nell'esecuzione dello script SQL: {e}")
        return False


def show_sample_queries():
    """Show some sample queries."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("\n=== ESEMPI DI QUERY ===")
        
        # 1. Ingredienti per categoria
        logger.info("1. Ingredienti per categoria:")
        cursor.execute(
            """
            SELECT ic.class_name, COUNT(*) as ingredient_count
            FROM ingredients i
            JOIN ingredient_classes ic ON i.class_id = ic.class_id
            GROUP BY ic.class_name
            ORDER BY ingredient_count DESC
            """
        )
        for row in cursor.fetchall():
            logger.info(f"  - {row[0]}: {row[1]} ingredienti")
        
        # 2. Totale ricette caricate
        logger.info("\n2. Totale ricette caricate:")
        cursor.execute("SELECT COUNT(*) FROM recipes")
        total_recipes = cursor.fetchone()[0]
        logger.info(f"  - {total_recipes} ricette")

        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error showing sample queries: {e}")
        return False
    
def load_csv_data():
    """Carica i dati dai CSV nelle tabelle usando psycopg2.copy_expert()."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        base_path = "data/processed/italian gastronomic recipes dataset/foods/CSV"

        # Assicura che le colonne temporanee esistano per l'import
        cursor.execute("ALTER TABLE ingredient_classes ADD COLUMN IF NOT EXISTS metaclass_name TEXT;")
        cursor.execute("ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS class_name TEXT;")
        conn.commit()

        copy_commands = [
            (
                "ingredients_metaclasses",
                f"{base_path}/ingredientsMetaclasses_translated.csv",
                "COPY ingredients_metaclasses (metaclass_name, metaclass_id) FROM STDIN WITH CSV HEADER DELIMITER ';'"
            ),
            (
                "ingredient_classes",
                f"{base_path}/ingredientsClasses_translated.csv",
                "COPY ingredient_classes (class_name, class_id, metaclass_name, metaclass_id) FROM STDIN WITH CSV HEADER DELIMITER ';'"
            ),
            (
                "ingredients",
                f"{base_path}/ingredients_translated.csv",
                "COPY ingredients (ingredient_name, ingredient_id, class_name, class_id) FROM STDIN WITH CSV HEADER DELIMITER ';'"
            ),
        ]

        for table, filepath, sql in copy_commands:
            with open(filepath, "r", encoding="utf-8") as f:
                cursor.copy_expert(sql, f)
            conn.commit()
            logger.info(f"Tabella {table} popolata da {os.path.basename(filepath)}")

        # Gestione speciale per recipes e recipe_ingredients: il CSV contiene molte più colonne
        recipes_path = f"{base_path}/recipes_translated.csv"
        with open(recipes_path, "r", encoding="utf-8") as rf:
            reader = csv.reader(rf, delimiter=';')
            try:
                header = next(reader)
            except StopIteration:
                raise ValueError("Il file recipes_translated.csv è vuoto")

            # Conserva solo le prime 8 colonne per la tabella recipes
            selected_count = 8
            selected_header = header[:selected_count]

            # Prepara buffer per COPY in recipes
            buf_recipes = io.StringIO()
            writer_recipes = csv.writer(buf_recipes, delimiter=';', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
            writer_recipes.writerow(selected_header)

            # Prepara buffer per COPY in recipe_ingredients (senza header)
            buf_ri = io.StringIO()
            writer_ri = csv.writer(buf_ri, delimiter=';', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
            # Nessun header: ordina colonne come (recipe_id, ingredient_id, quantity)

            # L’header del CSV contiene ripetizioni di colonne Ingrediente/ID/Quantità
            # Identifica le posizioni di tutte le triplette
            ingredient_triplets = []
            i = selected_count  # dopo le prime 8 colonne iniziano gli ingredienti
            while i + 2 < len(header):
                col1 = header[i].strip().lower()
                col2 = header[i+1].strip().lower()
                col3 = header[i+2].strip().lower()
                if ("ingrediente" in col1) and ("id" in col2) and ("quantit" in col3):
                    ingredient_triplets.append((i, i+1, i+2))
                    i += 3
                else:
                    # potrebbe essere la sezione “Preparazione;ID;Quantità”
                    # quando la incontriamo, ci fermiamo
                    break

            for row in reader:
                # Scrivi la parte ricetta (prime 8 colonne)
                row8 = (row + [''] * selected_count)[:selected_count]
                writer_recipes.writerow(row8)

                # Estrai tutte le triplette ingrediente
                for (c_name, c_id, c_qty) in ingredient_triplets:
                    # proteggi da righe corte
                    if c_id < len(row):
                        ing_id_raw = row[c_id].strip()
                        if ing_id_raw:
                            try:
                                ing_id = int(ing_id_raw)
                            except ValueError:
                                continue
                            qty = 1
                            if c_qty < len(row):
                                qty_raw = row[c_qty].strip()
                                if qty_raw:
                                    try:
                                        qty = int(qty_raw)
                                    except ValueError:
                                        qty = 1
                            # recipe_id è la seconda colonna (ID) tra le prime 8
                            try:
                                recipe_id = int(row[1])
                            except Exception:
                                continue
                            writer_ri.writerow([recipe_id, ing_id, qty])

            # COPY in recipes
            buf_recipes.seek(0)
            copy_sql_recipes = (
                "COPY recipes (recipe_name, recipe_id, recipe_link, category_name, category_id, cost, difficulty, preparation_time) "
                "FROM STDIN WITH CSV HEADER DELIMITER ';'"
            )
            cursor.copy_expert(copy_sql_recipes, buf_recipes)
            conn.commit()
            logger.info(f"Tabella recipes popolata da {os.path.basename(recipes_path)} (prime 8 colonne)")

            # COPY in recipe_ingredients
            buf_ri.seek(0)
            copy_sql_ri = (
                "COPY recipe_ingredients (recipe_id, ingredient_id, quantity) "
                "FROM STDIN WITH CSV DELIMITER ';'"
            )
            cursor.copy_expert(copy_sql_ri, buf_ri)
            conn.commit()
            logger.info("Tabella recipe_ingredients popolata dai campi ingrediente del CSV delle ricette")

        # cleanup colonne temporanee (idempotente)
        cursor.execute("ALTER TABLE ingredient_classes DROP COLUMN IF EXISTS metaclass_name;")
        cursor.execute("ALTER TABLE ingredients DROP COLUMN IF EXISTS class_name;")
        conn.commit()

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Errore durante il caricamento dei CSV: {e}")
        return False

# METODO PER ASSEGNARE IMMAGINI ALLE RICETTE (OPZIONALE)
def assign_recipe_images():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        images_dir = Path("./images")
        cursor.execute("SELECT recipe_id FROM recipes")
        recipe_ids = [row[0] for row in cursor.fetchall()]

        for rid in recipe_ids:
            img_path = images_dir / f"{rid}.jpg"
            if img_path.exists():
                cursor.execute(
                    "UPDATE recipes SET image_path = %s WHERE recipe_id = %s",
                    (str(img_path), rid)
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Immagini assegnate alle ricette con successo")
        return True
    except Exception as e:
        logger.error(f"Errore nell'assegnare le immagini: {e}")
        return False



def main():
    """Main function to execute the database population."""
    logger.info("=== AVVIO POPOLAMENTO DATABASE ===")
    
    # Check if CSV files exist
    csv_files = [
        'data/processed/italian gastronomic recipes dataset/foods/CSV/ingredientsMetaclasses_translated.csv',
        'data/processed/italian gastronomic recipes dataset/foods/CSV/ingredientsClasses_translated.csv',
        'data/processed/italian gastronomic recipes dataset/foods/CSV/ingredients_translated.csv',
        'data/processed/italian gastronomic recipes dataset/foods/CSV/recipes_translated.csv'
    ]
    
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            logger.error(f"File CSV mancante: {csv_file}")
            sys.exit(1)
        else:
            logger.info(f"✓ File CSV trovato: {os.path.basename(csv_file)}")
    
    # 1. Create database
    logger.info("\n1. Creazione database...")
    if not create_database():
        logger.error("Errore nella creazione del database")
        sys.exit(1)
    
    # 2. Execute SQL script (schema)
    logger.info("\n2. Esecuzione script SQL (schema)...")
    sql_script_path = Path(__file__).parent / 'database_setup.sql'
    if not execute_sql_script(sql_script_path):
        logger.error("Errore nell'esecuzione dello script SQL")
        sys.exit(1)

    # 3. Load CSV data
    logger.info("\n3. Caricamento CSV...")
    if not load_csv_data():
        logger.error("Errore nel caricamento dei dati CSV")
        sys.exit(1)

    # 4. Assign images
    logger.info("\n4. Assegnazione immagini...")
    if not assign_recipe_images():
        logger.error("Errore nell'assegnazione delle immagini")
        sys.exit(1)

    # 5. Esempi di query
    logger.info("\n5. Esempi di query...")
    if not show_sample_queries():
        logger.error("Errore nel mostrare le query di esempio")
        sys.exit(1)
    
    logger.info("\n=== DATABASE POPOLATO CON SUCCESSO! ===")
    logger.info(f"Database: {DB_CONFIG['database']}")
    logger.info(f"User: {DB_CONFIG['user']}")
    logger.info(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    logger.info("\nPuoi ora connetterti a PostgreSQL e verificare i dati!")

    # (rimosso: doppia esecuzione script SQL e caricamento CSV)



if __name__ == "__main__":
    main()