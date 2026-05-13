"""
airflow/dags/pulsetrack_pipeline.py
End-to-end DAG: Ingest → Load → Transform (dbt)
Runs every 6 hours.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "pulsetrack",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

DBT_PROJECT_DIR = "/opt/airflow/project/dbt_project"
DBT_PROFILES_DIR = "/opt/airflow/project/dbt_project/profiles"
DB_PATH = "/opt/airflow/project/data/pulsetrack.duckdb"


def ingest_github(**kwargs):
    import sys
    sys.path.insert(0, "/opt/airflow/project")
    from ingestion.github_ingest import run_ingestion
    count = run_ingestion()
    print(f"Ingested {count} repositories")


def load_to_db(**kwargs):
    import sys
    sys.path.insert(0, "/opt/airflow/project")
    from ingestion.load_to_duckdb import load_raw_to_duckdb
    load_raw_to_duckdb()


with DAG(
    dag_id="pulsetrack_pipeline",
    description="GitHub trending data pipeline — ingest, load, transform",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 */6 * * *",  # Every 6 hours
    catchup=False,
    tags=["pulsetrack", "github", "data-engineering"],
) as dag:

    t1_ingest = PythonOperator(
        task_id="ingest_github_api",
        python_callable=ingest_github,
    )

    t2_load = PythonOperator(
        task_id="load_raw_to_duckdb",
        python_callable=load_to_db,
    )

    t3_dbt = BashOperator(
        task_id="dbt_run_transforms",
        bash_command=(
            f"pip install dbt-duckdb --quiet && "
            f"cd {DBT_PROJECT_DIR} && "
            f"PULSETRACK_DB_PATH={DB_PATH} "
            f"dbt run --profiles-dir {DBT_PROFILES_DIR} --project-dir {DBT_PROJECT_DIR}"
        ),
    )

    t4_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"PULSETRACK_DB_PATH={DB_PATH} "
            f"dbt test --profiles-dir {DBT_PROFILES_DIR} --project-dir {DBT_PROJECT_DIR}"
        ),
    )

    t1_ingest >> t2_load >> t3_dbt >> t4_test
