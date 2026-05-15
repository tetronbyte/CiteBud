# CiteBud — Adaptive Study Assistant

A database-centric adaptive study assistant built on a RAG (Retrieval-Augmented Generation) pipeline. Students upload academic documents which are chunked, embedded, and stored in PostgreSQL with pgvector. The system generates grounded, citation-backed answers at three difficulty levels with query caching and per-student topic confidence tracking.

**Track:** A (RAG Pipeline)
**Database:** PostgreSQL 14+ with pgvector

---

## Quick Start (Reproduce from Scratch)

### Prerequisites

- PostgreSQL 14+ with the `pgvector` extension installed
- Python 3.10+
- pip

### Step-by-step Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd CiteBud

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Create the database and enable pgvector
createdb studydb
psql -d studydb -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 4. Load the schema (idempotent — safe to re-run)
psql -d studydb -f schema/schema.sql

# 5. Generate seed data (requires sentence-transformers model download on first run)
python data/seed_data.py

# 6. Load the seed data
psql -d studydb -f data/seed.sql

# 7. Run queries
psql -d studydb -f queries/queries.sql
```

### Environment Variables

If you need to connect to a non-default PostgreSQL instance:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGDATABASE=studydb
```

---

## Project Structure

```
CiteBud/
├── schema/
│   └── schema.sql           # DDL script (11 tables, indexes, constraints)
├── data/
│   ├── seed_data.py         # Python data generator
│   └── seed.sql             # Generated INSERT statements (output of seed_data.py)
├── queries/
│   └── queries.sql          # 10 labelled SQL queries (aggregations, joins, subqueries, CTEs, window functions)
├── requirements.txt         # Python dependencies
├── CLAUDE.md                # AI assistant context
├── milestone1_design.md     # ER diagram, 3NF justification, constraint rationale
├── milestone2_plan.md       # Milestone 2 planning document
└── README.md                # This file
```

---

## Data Dictionary

### Table: `students`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| student_id | SERIAL | PK | Auto-incrementing unique student identifier |
| email | VARCHAR(255) | NOT NULL, UNIQUE | Student email address (alternate key) |
| full_name | VARCHAR(120) | NOT NULL | Student's display name |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Account registration timestamp |

### Table: `documents`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| document_id | SERIAL | PK | Auto-incrementing document identifier |
| student_id | INTEGER | FK → students, NOT NULL | Owning student |
| title | VARCHAR(255) | NOT NULL, UNIQUE with student_id | Document title |
| course_code | VARCHAR(32) | nullable | Associated course (e.g., "CS3010") |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When the document was first created |

### Table: `document_versions`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| version_id | SERIAL | PK | Auto-incrementing version identifier |
| document_id | INTEGER | FK → documents, NOT NULL | Parent logical document |
| version_no | INTEGER | NOT NULL, CHECK ≥ 1, UNIQUE with document_id | Monotonic version counter |
| file_path | TEXT | NOT NULL | Storage path to the uploaded file |
| num_pages | INTEGER | NOT NULL, CHECK > 0 | Page count of this version |
| uploaded_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Upload timestamp |

### Table: `chunks`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| chunk_id | BIGSERIAL | PK | Auto-incrementing chunk identifier |
| version_id | INTEGER | FK → document_versions, NOT NULL | Which version this chunk belongs to |
| chunk_index | INTEGER | NOT NULL, CHECK ≥ 0, UNIQUE with version_id | Position within the document version |
| page_number | INTEGER | NOT NULL, CHECK ≥ 1 | Source page in the original document |
| content | TEXT | NOT NULL | Raw text content of the chunk |
| token_count | INTEGER | CHECK > 0 or NULL | Approximate token count |
| embedding | VECTOR(384) | NOT NULL | 384-dimensional embedding (all-MiniLM-L6-v2) |

### Table: `topics`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| topic_id | SERIAL | PK | Auto-incrementing topic identifier |
| name | VARCHAR(120) | NOT NULL, UNIQUE | Human-readable topic name |

### Table: `chunk_topics`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| chunk_id | BIGINT | PK (composite), FK → chunks | Tagged chunk |
| topic_id | INTEGER | PK (composite), FK → topics | Assigned topic |
| relevance | REAL | NOT NULL, CHECK [0.0, 1.0] | How strongly this chunk relates to the topic |

### Table: `solutions`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| solution_id | BIGSERIAL | PK | Auto-incrementing solution identifier |
| question_hash | CHAR(64) | NOT NULL, UNIQUE with difficulty | SHA-256 hash of normalized question text |
| difficulty | VARCHAR(16) | NOT NULL, CHECK IN (foundational, intermediate, advanced) | Target difficulty level |
| answer_text | TEXT | NOT NULL | Full LLM-generated answer |
| model_name | VARCHAR(100) | NOT NULL | Which model produced this answer |
| generated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Generation timestamp |

### Table: `queries`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| query_id | BIGSERIAL | PK | Auto-incrementing query identifier |
| student_id | INTEGER | FK → students, NOT NULL | Who asked the question |
| question_text | TEXT | NOT NULL | Original question as typed |
| question_hash | CHAR(64) | NOT NULL | SHA-256 of normalized question (for cache lookup) |
| difficulty | VARCHAR(16) | NOT NULL, CHECK IN (foundational, intermediate, advanced) | Requested difficulty |
| solution_id | BIGINT | FK → solutions, nullable | Resolved answer (NULL if pending) |
| was_cache_hit | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether this query reused a cached solution |
| asked_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When the question was asked |

### Table: `solution_citations`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| solution_id | BIGINT | PK (composite), FK → solutions | The answer being cited |
| chunk_id | BIGINT | PK (composite), FK → chunks | The source chunk cited |
| rank | INTEGER | NOT NULL, CHECK ≥ 1, UNIQUE with solution_id | Retrieval rank (1 = most relevant) |
| similarity_score | REAL | NOT NULL, CHECK [-1.0, 1.0] | Cosine similarity at retrieval time |

### Table: `feedback`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| feedback_id | BIGSERIAL | PK | Auto-incrementing feedback identifier |
| query_id | BIGINT | FK → queries, NOT NULL, UNIQUE | One rating per query |
| rating | SMALLINT | NOT NULL, CHECK [1, 5] | 1 = terrible, 5 = excellent |
| comment | TEXT | nullable | Optional free-text feedback |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When the feedback was submitted |

### Table: `user_topic_profile`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| student_id | INTEGER | PK (composite), FK → students | The profiled student |
| topic_id | INTEGER | PK (composite), FK → topics | The measured topic |
| confidence_score | REAL | NOT NULL, DEFAULT 0.0, CHECK [0.0, 1.0] | Estimated mastery (0 = none, 1 = full) |
| interactions_count | INTEGER | NOT NULL, DEFAULT 0, CHECK ≥ 0 | Number of interactions on this topic |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last profile update |

---

## Dataset Description

### Source
All data is **synthetically generated** by `data/seed_data.py` using:
- **Faker** library for realistic names and emails
- **Sentence-transformers** (all-MiniLM-L6-v2) for real 384-dimensional embeddings
- **Hand-written academic text templates** covering 30 topics across CS, Math, and Physics domains

### Generation Method
1. Students and documents are generated with Faker (seeded for reproducibility)
2. Chunk text is drawn from curated academic content templates (not random/lorem-ipsum)
3. Embeddings are computed by the actual sentence-transformer model on the real text
4. Questions, solutions, and citations maintain referential integrity throughout
5. Feedback ratings follow a realistic distribution (skewed toward 4-5 stars)
6. All random seeds are fixed (`seed=42`) for reproducibility

### Row Counts

| Table | Approximate Rows |
|-------|-----------------|
| students | 20 |
| documents | 50 |
| document_versions | ~60 |
| chunks | ~800 |
| topics | 30 |
| chunk_topics | ~1200 |
| solutions | 100 |
| queries | 150 |
| solution_citations | ~300 |
| feedback | 80 |
| user_topic_profile | 100 |
| **Total** | **~2900+** |

---

## SQL Queries Summary

The file `queries/queries.sql` contains 10 labelled queries demonstrating:

| # | Category | Description |
|---|----------|-------------|
| 1 | Aggregation | Average feedback rating per difficulty level |
| 2 | Aggregation | Monthly query volume per student |
| 3 | Join | Full query audit trail (question + answer + feedback) |
| 4 | Join | Chunks with source document and topic names |
| 5 | Subquery | Students with above-average confidence scores |
| 6 | Subquery | Topics appearing in more chunks than average |
| 7 | CTE | Cache hit rate per student |
| 8 | CTE | Top-cited chunks traced to source documents |
| 9 | Window Function | Student activity ranking (DENSE_RANK) |
| 10 | Window Function | Rolling 7-day average of feedback ratings |

---

## AI Usage Disclosure

- **Claude Code** (Anthropic): Used for code generation assistance, query design, and documentation drafting. All generated code was reviewed, tested, and adapted.
- **Sentence-transformers**: Used programmatically to generate real embeddings for chunk data (not for content generation).

---

## License

Academic project — not for redistribution.
