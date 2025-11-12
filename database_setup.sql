-- Setup schema
DROP TABLE IF EXISTS recipe_ingredients;
DROP TABLE IF EXISTS user_selected_recipes;
DROP TABLE IF EXISTS user_owned_ingredients;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS ingredient_classes;
DROP TABLE IF EXISTS ingredients_metaclasses;
-- (RIMOSSE) istruzioni DROP TABLE per preservare lo schema e i dati esistenti

-- Dictionaries
CREATE TABLE IF NOT EXISTS ingredients_metaclasses (
    metaclass_id INTEGER PRIMARY KEY,
    metaclass_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingredient_classes (
    class_id INTEGER PRIMARY KEY,
    class_name TEXT NOT NULL,
    metaclass_id INTEGER NOT NULL REFERENCES ingredients_metaclasses(metaclass_id),
    -- temporary during import (will be dropped)
    metaclass_name TEXT
);

CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id INTEGER PRIMARY KEY,
    ingredient_name TEXT NOT NULL,
    class_id INTEGER NOT NULL REFERENCES ingredient_classes(class_id),
    -- temporary during import (will be dropped)
    class_name TEXT
);

CREATE TABLE IF NOT EXISTS recipes (
    recipe_id INTEGER PRIMARY KEY,
    recipe_name TEXT NOT NULL,
    recipe_link TEXT,
    category_name TEXT,
    category_id INTEGER,
    cost INTEGER,
    difficulty INTEGER,
    preparation_time INTEGER,
    image_path TEXT
);

-- Junction (can be filled later)
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id INTEGER REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (recipe_id, ingredient_id)
);

-- Users and relations
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    nickname TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_selected_recipes (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    recipe_id INTEGER REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    selected_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, recipe_id)
);

CREATE TABLE IF NOT EXISTS user_owned_ingredients (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, ingredient_id)
);
