airflow_project/
├── .airflowignore             # Mencegah Airflow memindai file non-DAG (biar hemat CPU)
├── .gitignore                 # Mencegah log, venv, dan file sensitif terunggah ke Git
├── README.md                  # Dokumentasi utama repositori
├── requirements.txt           # Daftar library Python tambahan yang dibutuhkan
│
├── config/                    # Konfigurasi global & variabel lingkungan
│   ├── airflow.cfg            # File konfigurasi utama Airflow
│   └── connections.json       # Template koneksi/variable (JANGAN diisi password asli)
│
├── dags/                      # Dags Folder (Folder utama yang didaftarkan ke Airflow)
│   ├── common/                # Shared code / utility yang dipakai LINTAS PROYEK
│   │   ├── hooks/             # Custom hook (misal: koneksi API internal)
│   │   ├── operators/         # Custom operator bawaan tim
│   │   └── utils/             # Helper fungsi umum (misal: notifier Slack/Email)
│   │
│   ├── project_sales/         # PROYEK 1: Sales Data Pipeline
│   │   ├── dag_sales_daily.py
│   │   ├── dag_sales_monthly.py
│   │   └── src/               # Logika bisnis khusus proyek Sales
│   │       ├── sql/           # Query SQL proyek Sales
│   │       └── transform.py   # Skrip pemrosesan Pandas/PySpark
│   │
│   ├── project_finance/       # PROYEK 2: Finance & Accounting
│   │   ├── dag_tax_report.py
│   │   └── src/
│   │       ├── sql/
│   │       └── excel_parser.py
│   │
│   └── project_inventory/     # PROYEK 3: Logistics & Inventory
│       ├── dag_stock_alert.py
│       └── src/
│           └── api_client.py
│
├── include/                   # Tempat menyimpan file aset statis/besar
│   ├── sql/                   # Query SQL global jika tidak masuk ke folder proyek
│   └── templates/             # Template email, HTML report, dsb.
│
├── plugins/                   # Airflow Plugins resmi (Custom UI, Webserver extensions)
│   └── custom_plugin.py
│
├── scripts/                   # Skrip otomatisasi lokal & deployment
│   ├── entrypoint.sh          # Skrip startup untuk Docker/Linux
│   └── init_connections.sh    # Skrip untuk otomatis membuat Airflow Connections/Variables
│
└── tests/                     # Unit Testing & Integration Testing
    ├── dags/                  # Tes untuk memvalidasi syntax DAG (bebas dari error import)
    │   ├── test_dag_integrity.py
    │   └── test_sales_dags.py
    └── unit/                  # Tes fungsi logika bisnis di dalam folder src/
        └── test_transform.py
