# CiteBud — Milestone 2 Setup Guide (For Friends)

**Deadline: 15 May 2026, 23:59 EAT**
**What we're submitting:** Database with seed data + 10 SQL queries + README

Everything is already built. You just need to set it up, verify it works, and submit.

---

## STEP 1: Install Prerequisites (~10 min)

### PostgreSQL
1. Download and install PostgreSQL 14+ from: https://www.postgresql.org/download/
2. During installation:
   - Remember the password you set for the `postgres` user
   - Keep the default port (5432)
   - Make sure "Command Line Tools" is checked
3. After install, open a terminal and verify:
   ```
   psql --version
   ```

### pgvector Extension
This is required for storing vector embeddings.

**Windows:**
- Download the latest release from: https://github.com/pgvector/pgvector/releases
- Follow Windows install instructions at: https://github.com/pgvector/pgvector#windows

**Mac:**
```bash
brew install pgvector
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql-14-pgvector
```

### Python 3.10+
- Download from https://www.python.org/downloads/ if not already installed
- Verify: `python --version`

---

## STEP 2: Clone and Install Dependencies (~5 min)

```bash
git clone https://github.com/tetronbyte/CiteBud.git
cd CiteBud
pip install -r requirements.txt
```

The first time you run the seed script (Step 4), it will also download a ~90MB AI model. This is normal.

---

## STEP 3: Create Database and Load Schema (~2 min)

Open a terminal and run:

```bash
createdb studydb
psql -d studydb -f schema/schema.sql
```

If `createdb` doesn't work, try:
```bash
psql -U postgres -c "CREATE DATABASE studydb;"
psql -U postgres -d studydb -f schema/schema.sql
```

You should see output like `CREATE TABLE`, `CREATE INDEX`, etc. with no errors.

---

## STEP 4: Load Seed Data (~1 min)

The seed data file (`data/seed.sql`) is already generated and committed. Just load it:

```bash
psql -d studydb -f data/seed.sql
```

If you get connection errors, use:
```bash
psql -U postgres -d studydb -f data/seed.sql
```

This inserts ~2937 rows across 11 tables.

**Optional:** If you want to regenerate the seed data yourself:
```bash
python data/seed_data.py
psql -d studydb -f data/seed.sql
```

---

## STEP 5: Run Queries and Verify (~2 min)

```bash
psql -d studydb -f queries/queries.sql
```

You should see **10 result sets** with actual data. No errors.

If you want to run queries one at a time interactively:
```bash
psql -d studydb
```
Then copy-paste individual queries from `queries/queries.sql`.

---

## STEP 6: Submit

- ZIP the entire `CiteBud/` folder (or just share the GitHub link)
- Submit on Google Classroom before 23:59 EAT

---

## Troubleshooting

### "psql: command not found"
Add PostgreSQL bin directory to your PATH:
- **Windows:** `C:\Program Files\PostgreSQL\14\bin`
- **Mac/Linux:** Usually added automatically

### "extension 'vector' is not available"
pgvector isn't installed. Go back to Step 1 and install the pgvector extension.

### "FATAL: password authentication failed"
Use `-U postgres` and enter the password you set during PostgreSQL installation:
```bash
psql -U postgres -d studydb -f schema/schema.sql
```

### "database 'studydb' does not exist"
Run: `createdb studydb` or `psql -U postgres -c "CREATE DATABASE studydb;"`

### "relation already exists" warnings
That's fine — the schema script drops and recreates tables. Safe to ignore.

---

## What's in the Repo

```
CiteBud/
├── schema/schema.sql         ← 11 tables with constraints and indexes
├── data/seed_data.py         ← Python script that generates seed data
├── data/seed.sql             ← 2937 rows of INSERT statements (pre-generated)
├── queries/queries.sql       ← 10 SQL queries (what gets graded)
├── README.md                 ← Data dictionary + full documentation
├── requirements.txt          ← Python dependencies
├── milestone2_plan.md        ← Planning doc
└── CLAUDE.md                 ← Ignore this (AI assistant config)
```

---

## Grading Criteria (so you know what matters)

| Marks | What | Are we good? |
|-------|------|-------------|
| 10 | Dataset: 1000+ rows, realistic data | YES — 2937 rows, real embeddings |
| 10 | Query coverage: 2 agg, 2 join, 2 subquery, 2 CTE, 2 window | YES — all covered |
| 10 | Query correctness: all return meaningful results | VERIFY THIS (Step 5) |
| 5 | Code quality: formatted, commented, named | YES — all queries labelled |
| 5 | README: clear repro instructions | YES — full data dictionary included |
