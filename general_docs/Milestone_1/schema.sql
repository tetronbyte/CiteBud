-- =====================================================================
-- CiteBud  -  Adaptive Study Assistant (RAG Pipeline)
-- Schema & DDL
-- Target: PostgreSQL 14+ with the `pgvector` extension
-- Run:    psql -d studydb -f schema.sql
-- =====================================================================
-- Design goals:
--   * DB-first: relational core, vector search as a column type
--   * Versioned document collections
--   * Topic-tagged chunks (M:N) for fine-grained retrieval & analytics
--   * Query caching via content-hash reuse of a single solution row
--   * Citation tracking with per-retrieval similarity scores
--   * Feedback loop + per-student / per-topic confidence profile
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- Drop in FK-safe order so the script is idempotent during development.
DROP TABLE IF EXISTS user_topic_profile  CASCADE;
DROP TABLE IF EXISTS feedback            CASCADE;
DROP TABLE IF EXISTS solution_citations  CASCADE;
DROP TABLE IF EXISTS queries             CASCADE;
DROP TABLE IF EXISTS solutions           CASCADE;
DROP TABLE IF EXISTS chunk_topics        CASCADE;
DROP TABLE IF EXISTS topics              CASCADE;
DROP TABLE IF EXISTS chunks              CASCADE;
DROP TABLE IF EXISTS document_versions   CASCADE;
DROP TABLE IF EXISTS documents           CASCADE;
DROP TABLE IF EXISTS students            CASCADE;


-- ---------------------------------------------------------------------
-- 1. students
-- End users of the assistant. Deliberately minimal - auth is out of scope.
-- ---------------------------------------------------------------------
CREATE TABLE students (
    student_id  SERIAL       PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,     -- alternate key
    full_name   VARCHAR(120) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE students IS 'Registered users who upload notes and ask questions.';


-- ---------------------------------------------------------------------
-- 2. documents
-- A LOGICAL document (e.g. "CS3010 Week 4 Notes"). Its actual content
-- lives in document_versions - this row is the stable identity that
-- survives re-uploads.
-- ---------------------------------------------------------------------
CREATE TABLE documents (
    document_id  SERIAL       PRIMARY KEY,
    student_id   INTEGER      NOT NULL
                 REFERENCES students(student_id) ON DELETE CASCADE,
    title        VARCHAR(255) NOT NULL,
    course_code  VARCHAR(32),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, title)                    -- per-student titles are unique
);
COMMENT ON TABLE documents IS
  'Logical document identity; concrete bytes live in document_versions.';


-- ---------------------------------------------------------------------
-- 3. document_versions
-- Each physical upload of a document. Enables the "versioning system"
-- feature: re-uploading a revised PDF creates a new version row, old
-- chunks stay intact so prior answers remain reproducible.
-- ---------------------------------------------------------------------
CREATE TABLE document_versions (
    version_id   SERIAL       PRIMARY KEY,
    document_id  INTEGER      NOT NULL
                 REFERENCES documents(document_id) ON DELETE CASCADE,
    version_no   INTEGER      NOT NULL CHECK (version_no >= 1),
    file_path    TEXT         NOT NULL,
    num_pages    INTEGER      NOT NULL CHECK (num_pages > 0),
    uploaded_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, version_no)
);
COMMENT ON TABLE document_versions IS
  'Immutable snapshots of a document; supports reproducible retrieval over time.';


-- ---------------------------------------------------------------------
-- 4. chunks
-- Embedded text fragments - the retrieval corpus. Belong to a specific
-- version so old answers can be replayed against the exact text that
-- generated them. 384 dims = all-MiniLM-L6-v2.
-- ---------------------------------------------------------------------
CREATE TABLE chunks (
    chunk_id     BIGSERIAL    PRIMARY KEY,
    version_id   INTEGER      NOT NULL
                 REFERENCES document_versions(version_id) ON DELETE CASCADE,
    chunk_index  INTEGER      NOT NULL CHECK (chunk_index >= 0),
    page_number  INTEGER      NOT NULL CHECK (page_number >= 1),
    content      TEXT         NOT NULL,
    token_count  INTEGER      CHECK (token_count IS NULL OR token_count > 0),
    embedding    VECTOR(384)  NOT NULL,
    UNIQUE (version_id, chunk_index)
);
COMMENT ON TABLE  chunks IS  'Embedded text fragments; queried via cosine distance.';
COMMENT ON COLUMN chunks.embedding IS 'Sentence-transformer vector; use the <=> operator.';

-- ANN index for vector search (hybrid retrieval's semantic half).
CREATE INDEX chunks_embedding_cos_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- B-Tree index on version_id supports per-document filtering and
-- provides execution-plan evidence of B-Tree index use.
CREATE INDEX chunks_version_idx ON chunks(version_id);


-- ---------------------------------------------------------------------
-- 5. topics
-- Controlled vocabulary of subject topics extracted from chunks.
-- Kept as a separate entity so analytics and user profiles can key on it.
-- ---------------------------------------------------------------------
CREATE TABLE topics (
    topic_id  SERIAL       PRIMARY KEY,
    name      VARCHAR(120) NOT NULL UNIQUE
);
COMMENT ON TABLE topics IS 'Extracted topics used for tagging chunks and profiling students.';


-- ---------------------------------------------------------------------
-- 6. chunk_topics  (junction, M:N between chunks and topics)
-- ---------------------------------------------------------------------
CREATE TABLE chunk_topics (
    chunk_id   BIGINT  NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    topic_id   INTEGER NOT NULL REFERENCES topics(topic_id) ON DELETE CASCADE,
    relevance  REAL    NOT NULL CHECK (relevance BETWEEN 0.0 AND 1.0),
    PRIMARY KEY (chunk_id, topic_id)
);
COMMENT ON TABLE chunk_topics IS
  'M:N tagging of chunks with topics; relevance is a property of the pairing.';


-- ---------------------------------------------------------------------
-- 7. solutions
-- An LLM-generated answer. Stored independently of queries so multiple
-- queries with the same hash+difficulty can reuse one solution row -
-- this IS the query cache. No separate cache table needed.
-- ---------------------------------------------------------------------
CREATE TABLE solutions (
    solution_id    BIGSERIAL    PRIMARY KEY,
    question_hash  CHAR(64)     NOT NULL,         -- SHA-256 of normalized question
    difficulty     VARCHAR(16)  NOT NULL
                   CHECK (difficulty IN ('foundational','intermediate','advanced')),
    answer_text    TEXT         NOT NULL,
    model_name     VARCHAR(100) NOT NULL,
    generated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (question_hash, difficulty)            -- cache lookup key
);
COMMENT ON TABLE solutions IS
  'Reusable LLM answers. UNIQUE(question_hash, difficulty) makes this the cache.';


-- ---------------------------------------------------------------------
-- 8. queries
-- Every question a student asks. Points at the solution it resolved to;
-- cache hits simply reuse an existing solution_id instead of inserting.
-- ---------------------------------------------------------------------
CREATE TABLE queries (
    query_id       BIGSERIAL   PRIMARY KEY,
    student_id     INTEGER     NOT NULL
                   REFERENCES students(student_id) ON DELETE CASCADE,
    question_text  TEXT        NOT NULL,
    question_hash  CHAR(64)    NOT NULL,
    difficulty     VARCHAR(16) NOT NULL
                   CHECK (difficulty IN ('foundational','intermediate','advanced')),
    solution_id    BIGINT      REFERENCES solutions(solution_id) ON DELETE SET NULL,
    was_cache_hit  BOOLEAN     NOT NULL DEFAULT FALSE,
    asked_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX queries_hash_diff_idx ON queries(question_hash, difficulty);
COMMENT ON TABLE queries IS
  'Audit log of questions. solution_id may be shared across queries (cache reuse).';


-- ---------------------------------------------------------------------
-- 9. solution_citations  (junction, M:N between solutions and chunks)
-- Records exactly which chunks grounded each answer, with the retrieval
-- rank and similarity score at the moment the answer was generated.
-- ---------------------------------------------------------------------
CREATE TABLE solution_citations (
    solution_id       BIGINT  NOT NULL
                      REFERENCES solutions(solution_id) ON DELETE CASCADE,
    chunk_id          BIGINT  NOT NULL
                      REFERENCES chunks(chunk_id) ON DELETE RESTRICT,
    rank              INTEGER NOT NULL CHECK (rank >= 1),
    similarity_score  REAL    NOT NULL CHECK (similarity_score BETWEEN -1.0 AND 1.0),
    PRIMARY KEY (solution_id, chunk_id),
    UNIQUE (solution_id, rank)                    -- no ties at the same rank
);
COMMENT ON TABLE solution_citations IS
  'Explainability backbone: links each answer to the exact chunks that grounded it.';


-- ---------------------------------------------------------------------
-- 10. feedback
-- Student rating of an answer. Keyed per query (not per solution) so the
-- same cached solution can receive different ratings from different asks.
-- ---------------------------------------------------------------------
CREATE TABLE feedback (
    feedback_id  BIGSERIAL   PRIMARY KEY,
    query_id     BIGINT      NOT NULL UNIQUE    -- one rating per query
                 REFERENCES queries(query_id) ON DELETE CASCADE,
    rating       SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment      TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE feedback IS 'User ratings; drives the retrieval-quality feedback loop.';


-- ---------------------------------------------------------------------
-- 11. user_topic_profile
-- Per-student confidence per topic. Composite PK (student, topic) - this
-- is a genuine associative entity, not a junction, because it carries
-- its own non-key attributes (confidence, counters, timestamps).
-- ---------------------------------------------------------------------
CREATE TABLE user_topic_profile (
    student_id          INTEGER     NOT NULL
                        REFERENCES students(student_id) ON DELETE CASCADE,
    topic_id            INTEGER     NOT NULL
                        REFERENCES topics(topic_id) ON DELETE CASCADE,
    confidence_score    REAL        NOT NULL DEFAULT 0.0
                        CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    interactions_count  INTEGER     NOT NULL DEFAULT 0
                        CHECK (interactions_count >= 0),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (student_id, topic_id)
);
COMMENT ON TABLE user_topic_profile IS
  'Adaptive learning signal: tracks each student''s mastery per topic.';

-- =====================================================================
-- End of schema.sql
-- =====================================================================
