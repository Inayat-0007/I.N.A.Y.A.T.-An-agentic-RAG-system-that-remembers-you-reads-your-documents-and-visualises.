# Sample documents (not indexed automatically)

These files are **MIT-licensed** demonstration content shipped with the repo. They are **not** placed under a real user profile and are **not** indexed until you copy them.

## How to use

1. Choose a profile name (e.g. `demo_user`).
2. Copy all files from this folder into `data/documents/{your_name}/`:

   ```bash
   mkdir -p data/documents/demo_user
   cp data/documents/_samples/*.pdf data/documents/_samples/*.txt data/documents/demo_user/
   ```

   On Windows PowerShell:

   ```powershell
   New-Item -ItemType Directory -Force -Path data\documents\demo_user
   Copy-Item data\documents\_samples\* -Destination data\documents\demo_user\
   ```

3. Rebuild the index for that profile (Streamlit sidebar, API upload, or `build_index("demo_user")`).
4. Ask: **"Who is the CEO of INAYAT AI Solutions?"** — the answer should cite **Dr. Inayat Hussain** from `inayat_company_facts.pdf`.

## Files

| File | Purpose |
|------|---------|
| `inayat_company_facts.pdf` | Deterministic CEO fact for RAG demos and `test_agent_query_rag` |
| `inayat_product_overview.pdf` | Short product description for multi-doc indexing |
| `inayat_glossary.txt` | Plain-text glossary (TXT ingestion) |
