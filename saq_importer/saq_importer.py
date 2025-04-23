import json
import psycopg2
import os
import logging
from datetime import datetime
from psycopg2.extras import Json

# Database config — adjust these
DB_CONFIG = {
    "dbname": "saq_db",
    "user": "postgres",
    "password": "testing",
    "host": "localhost",
    "port": 5432,
}

PRODUCTS_JSON = os.path.join("run", "products.json")
DETAILS_JSON = os.path.join("run", "details", "product_details.json")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )


def connect_db():
    return psycopg2.connect(**DB_CONFIG)


def create_tables(conn):
    with conn.cursor() as cur:
        # 1) the “current” products table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                code_saq           TEXT        PRIMARY KEY,
                name               TEXT,
                url                TEXT,
                type               TEXT,
                volume             TEXT,
                country            TEXT,
                rating_pct         INTEGER,
                reviews_count      INTEGER,
                discounted         BOOLEAN,
                discount_pct       TEXT,
                price              REAL,
                old_price          REAL,
                available_online   BOOLEAN,
                available_instore  BOOLEAN,
                categories         JSONB
            );
        """)

        # 2) history of every change
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products_history (
                code_saq TEXT,
                name TEXT,
                url TEXT,
                type TEXT,
                volume TEXT,
                country TEXT,
                rating_pct INTEGER,
                reviews_count INTEGER,
                discounted BOOLEAN,
                discount_pct TEXT,
                price REAL,
                old_price REAL,
                available_online BOOLEAN,
                available_instore BOOLEAN,
                categories JSONB,
                valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                valid_to   TIMESTAMPTZ,
                PRIMARY KEY (code_saq, valid_from)
            );
        """)

        # 3) extended attributes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS product_attributes (
                code_saq   TEXT    PRIMARY KEY,
                attributes JSONB
            );
        """)

        conn.commit()


def import_products(conn, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    logging.info(f"Importing {len(products)} products with history tracking...")

    with conn.cursor() as cur:
        for code_saq, product in products.items():
            cur.execute("SELECT * FROM products WHERE code_saq = %s", (code_saq,))
            existing = cur.fetchone()

            # Prepare product values
            values = {
                **product,
                "categories": Json(product.get("categories", []))
            }

            # Check if anything changed
            should_insert_history = False
            if existing:
                columns = [desc[0] for desc in cur.description]
                current = dict(zip(columns, existing))
                for key in values:
                    if key in current and values[key] != current[key]:
                        should_insert_history = True
                        break
            else:
                should_insert_history = True

            # Update main table
            cur.execute("""
                INSERT INTO products (
                    code_saq, name, url, type, volume, country,
                    rating_pct, reviews_count, discounted, discount_pct,
                    price, old_price, available_online, available_instore,
                    categories
                ) VALUES (
                    %(code_saq)s, %(name)s, %(url)s, %(type)s, %(volume)s, %(country)s,
                    %(rating_pct)s, %(reviews_count)s, %(discounted)s, %(discount_pct)s,
                    %(price)s, %(old_price)s, %(available_online)s, %(available_instore)s,
                    %(categories)s
                )
                ON CONFLICT (code_saq) DO UPDATE SET
                    name = EXCLUDED.name,
                    price = EXCLUDED.price,
                    old_price = EXCLUDED.old_price,
                    discounted = EXCLUDED.discounted,
                    discount_pct = EXCLUDED.discount_pct,
                    available_online = EXCLUDED.available_online,
                    available_instore = EXCLUDED.available_instore,
                    categories = EXCLUDED.categories;
            """, values)

            if should_insert_history:
                # Expire previous version
                cur.execute("""
                    UPDATE products_history
                    SET valid_to = NOW()
                    WHERE code_saq = %s AND valid_to IS NULL;
                """, (code_saq,))

                # Insert new version
                cur.execute("""
                    INSERT INTO products_history (
                        code_saq, name, url, type, volume, country,
                        rating_pct, reviews_count, discounted, discount_pct,
                        price, old_price, available_online, available_instore,
                        categories, valid_from
                    ) VALUES (
                        %(code_saq)s, %(name)s, %(url)s, %(type)s, %(volume)s, %(country)s,
                        %(rating_pct)s, %(reviews_count)s, %(discounted)s, %(discount_pct)s,
                        %(price)s, %(old_price)s, %(available_online)s, %(available_instore)s,
                        %(categories)s, NOW()
                    );
                """, values)

    conn.commit()
    logging.info("Finished importing products with history.")


def import_product_details(conn, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        details = json.load(f)

    logging.info(f"Importing attributes for {len(details)} products into 'product_attributes' table...")

    with conn.cursor() as cur:
        for code_saq, attributes in details.items():
            cur.execute("""
                INSERT INTO product_attributes (
                    code_saq, attributes
                )
                VALUES (
                    %s, %s
                )
                ON CONFLICT (code_saq) DO UPDATE SET
                    attributes = EXCLUDED.attributes;
            """, (code_saq, Json(attributes)))

    conn.commit()
    logging.info("Finished importing product attributes.")


if __name__ == "__main__":
    setup_logging()
    conn = connect_db()
    create_tables(conn)
    import_products(conn, PRODUCTS_JSON)
    import_product_details(conn, DETAILS_JSON)
    conn.close()
