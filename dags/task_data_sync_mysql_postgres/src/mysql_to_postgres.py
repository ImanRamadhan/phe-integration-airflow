#!/usr/bin/env python
# coding: utf-8

# In[1]:


import logging
from typing import List, Tuple

import pymysql
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch

from src.config import MYSQL_CONFIG, POSTGRES_CONFIG


# In[2]:


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# In[3]:


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_mysql_connection():
    """
    Create MySQL source connection.
    """
    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False
    )

def get_postgres_connection():
    """
    Create PostgreSQL target connection.
    """
    return psycopg2.connect(
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"],
        database=POSTGRES_CONFIG["database"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"]
    )


# In[4]:


with get_mysql_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        result = cursor.fetchone()
    print("MySQL version is: ", result[0])


# In[5]:


with get_postgres_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        result = cursor.fetchone()
    print("PostgreSQL version is: ", result[0])


# In[6]:


# ============================================================
# EXTRACT
# ============================================================

def extract_from_mysql(
    connection,
    source_table: str
) -> Tuple[List[str], List[tuple]]:

    logger.info(
        "Extracting data from MySQL table: %s",
        source_table
    )

    query = f"SELECT * FROM {source_table}"

    with connection.cursor() as cursor:

        cursor.execute(query)

        columns = [
            column[0]
            for column in cursor.description
        ]

        rows = cursor.fetchall()

    logger.info(
        "Extracted %s rows from MySQL",
        len(rows)
    )

    return columns, rows


# In[11]:


# ============================================================
# GET EXISTING IDS FROM POSTGRES
# ============================================================

def get_existing_ids(
    connection,
    target_table: str,
    id_column: str
) -> set:

    logger.info(
        "Checking existing IDs in PostgreSQL table: %s",
        target_table
    )

    query = sql.SQL("""
        SELECT {}
        FROM {}
    """).format(
        sql.Identifier(id_column),
        sql.Identifier(target_table)
    )

    with connection.cursor() as cursor:

        cursor.execute(query)

        rows = cursor.fetchall()

    existing_ids = {
        row[0]
        for row in rows
    }

    logger.info(
        "Found %s existing IDs in PostgreSQL",
        len(existing_ids)
    )

    return existing_ids


# In[12]:


# ============================================================
# FILTER NEW ROWS
# ============================================================

def filter_new_rows(
    columns: List[str],
    rows: List[tuple],
    existing_ids: set,
    id_column: str
) -> List[tuple]:

    id_index = columns.index(id_column)

    new_rows = [
        row
        for row in rows
        if row[id_index] not in existing_ids
    ]

    logger.info(
        "New rows to insert: %s",
        len(new_rows)
    )

    return new_rows


# In[13]:


# ============================================================
# LOAD
# ============================================================

def load_to_postgres(
    connection,
    target_table: str,
    columns: List[str],
    rows: List[tuple]
):
    if not rows:
        logger.info(
            "No data to load into PostgreSQL."
        )
        return
    logger.info(
        "Loading %s new rows into PostgreSQL table: %s",
        len(rows),
        target_table
    )

    column_identifiers = [
        sql.Identifier(column)
        for column in columns
    ]

    placeholders = sql.SQL(", ").join(
        sql.SQL("%s")
        for _ in columns
    )

    query = sql.SQL("""
        INSERT INTO {} ({})
        VALUES ({})
    """).format(
        sql.Identifier(target_table),
        sql.SQL(", ").join(column_identifiers),
        placeholders
    )

    with connection.cursor() as cursor:

        execute_batch(
            cursor,
            query.as_string(connection),
            rows,
            page_size=1000
        )

    logger.info(
        "Successfully loaded %s rows into PostgreSQL.",
        len(rows)
    )

    return len(rows)


# In[17]:


# ============================================================
# MAIN INGESTION
# ============================================================

def ingest(
    source_table: str,
    target_table: str,
    id_column: str = "transaction_id"
):
    mysql_connection = None
    postgres_connection = None

    try:
        logger.info("========================================")
        logger.info("Starting MySQL -> PostgreSQL ingestion")
        logger.info("Source : %s", source_table)
        logger.info("Target : %s", target_table)
        logger.info("ID     : %s", id_column)
        logger.info("========================================")

        # --------------------------------------------
        # CONNECT MYSQL
        # --------------------------------------------

        logger.info("Connecting to MySQL...")

        mysql_connection = get_mysql_connection()

        logger.info(
            "MySQL connection successful!"
        )

        # --------------------------------------------
        # CONNECT POSTGRES
        # --------------------------------------------

        logger.info(
            "Connectiong to PostgreSQL..."
        )

        postgres_connection = get_postgres_connection()

        logger.info(
            "PostgreSQL connection successful!"
        )

        # --------------------------------------------
        # EXTRACT
        # --------------------------------------------

        columns, rows = extract_from_mysql(
            mysql_connection,
            source_table
        )

        if not rows:
            logger.info("Source table contains no data.")

            return

        # ----------------------------------------------------
        # GET EXISTING TARGET IDS
        # ----------------------------------------------------

        existing_ids = get_existing_ids(
            postgres_connection,
            target_table,
            id_column
        )

        # ----------------------------------------------------
        # FILTER NEW DATA
        # ----------------------------------------------------

        new_rows = filter_new_rows(
            columns,
            rows,
            existing_ids,
            id_column
        )

        # --------------------------------------------
        # LOAD
        # --------------------------------------------

        inserted_rows = load_to_postgres(
            postgres_connection,
            target_table,
            columns,
            new_rows
        )

        # --------------------------------------------
        # COMMIT
        # --------------------------------------------

        postgres_connection.commit()

        logger.info(
            "PosgreSQL transaction committed!"
        )

        logger.info(
            "Total rows inserted: %s",
            inserted_rows
        )

        logger.info("========================================")
        logger.info("INGESTION SUCCESS")
        logger.info("========================================")

    except Exception as e:
        logger.exception(
            "Ingestion failed: %s",
            e
        )

        if postgres_connection:
            postgres_connection.rollback()

            logger.info(
                "PostgreSQL transaction rolled back"
            )
        raise

    finally:

        if mysql_connection:
            mysql_connection.close()

            logger.info(
                "MySQL connection closed."
            )

        if postgres_connection:
            postgres_connection.close()

            logger.info(
                "PostgreSQL connection closed."
            )


# In[19]:


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    ingest(
        source_table="transactions",
        target_table="stg_transactions",
        id_column="transaction_id"
    )

