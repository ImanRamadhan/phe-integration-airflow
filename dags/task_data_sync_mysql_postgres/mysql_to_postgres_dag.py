from datetime import datetime
import sys

from airflow.decorators import dag, task


# ============================================================
# PROJECT PATH
# ============================================================

sys.path.append(
    "/home/jo/airflow_project/dags/task_data_sync_mysql_postgres"
)


from src.mysql_to_postgres import ingest


# ============================================================
# DAG
# ============================================================

@dag(
    dag_id="new_mysql_to_postgres_ingestion",
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    tags=["dev", "sync", "mysql", "postgres"],
)
def mysql_to_postgres_dag():

    @task
    def run_ingestion():

        ingest(
            source_table="transactions",
            target_table="stg_transactions",
            id_column="transaction_id"
        )


    run_ingestion()


mysql_to_postgres_dag()
