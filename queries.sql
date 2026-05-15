-- =====================================================================
-- CiteBud — Milestone 2: SQL Queries
-- =====================================================================
-- Each query is labelled with its category, purpose, and expected output.
-- All queries run on a fresh database loaded with schema.sql + seed.sql.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 1: AGGREGATION
-- Average feedback rating per difficulty level
-- Purpose: Understand which difficulty levels produce better-rated answers
-- ─────────────────────────────────────────────────────────────────────
SELECT
    q.difficulty,
    COUNT(f.feedback_id)       AS total_ratings,
    ROUND(AVG(f.rating), 2)   AS avg_rating,
    MIN(f.rating)              AS min_rating,
    MAX(f.rating)              AS max_rating
FROM queries q
JOIN feedback f ON f.query_id = q.query_id
GROUP BY q.difficulty
ORDER BY avg_rating DESC;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 2: AGGREGATION
-- Monthly query volume per student (top 5 most active students)
-- Purpose: Track usage trends and identify power users
-- ─────────────────────────────────────────────────────────────────────
SELECT
    s.full_name,
    DATE_TRUNC('month', q.asked_at)  AS month,
    COUNT(*)                         AS queries_asked
FROM queries q
JOIN students s ON s.student_id = q.student_id
GROUP BY s.full_name, DATE_TRUNC('month', q.asked_at)
HAVING COUNT(*) >= 2
ORDER BY month, queries_asked DESC;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 3: JOIN
-- Full query audit trail: question, answer, and feedback in one view
-- Purpose: End-to-end traceability for a student's interaction
-- ─────────────────────────────────────────────────────────────────────
SELECT
    s.full_name                    AS student,
    q.question_text,
    q.difficulty,
    LEFT(sol.answer_text, 100)     AS answer_preview,
    f.rating,
    f.comment                      AS feedback_comment
FROM queries q
JOIN students s        ON s.student_id = q.student_id
JOIN solutions sol     ON sol.solution_id = q.solution_id
LEFT JOIN feedback f   ON f.query_id = q.query_id
ORDER BY q.asked_at DESC
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 4: JOIN
-- Chunks with their source document title and associated topic names
-- Purpose: Verify the document → version → chunk → topic chain
-- ─────────────────────────────────────────────────────────────────────
SELECT
    d.title                 AS document_title,
    d.course_code,
    dv.version_no,
    c.chunk_id,
    LEFT(c.content, 80)     AS chunk_preview,
    t.name                  AS topic_name,
    ct.relevance
FROM chunks c
JOIN document_versions dv  ON dv.version_id = c.version_id
JOIN documents d           ON d.document_id = dv.document_id
JOIN chunk_topics ct       ON ct.chunk_id = c.chunk_id
JOIN topics t              ON t.topic_id = ct.topic_id
ORDER BY d.title, c.chunk_index
LIMIT 30;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 5: SUBQUERY
-- Students whose average confidence score is above the global average
-- Purpose: Identify high-performing students for analytics
-- ─────────────────────────────────────────────────────────────────────
SELECT
    s.student_id,
    s.full_name,
    ROUND(AVG(utp.confidence_score)::numeric, 3) AS avg_confidence
FROM students s
JOIN user_topic_profile utp ON utp.student_id = s.student_id
GROUP BY s.student_id, s.full_name
HAVING AVG(utp.confidence_score) > (
    SELECT AVG(confidence_score) FROM user_topic_profile
)
ORDER BY avg_confidence DESC;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 6: SUBQUERY
-- Topics that appear in more chunks than the average topic
-- Purpose: Find the most broadly covered topics in the corpus
-- ─────────────────────────────────────────────────────────────────────
SELECT
    t.topic_id,
    t.name,
    COUNT(ct.chunk_id) AS chunk_count
FROM topics t
JOIN chunk_topics ct ON ct.topic_id = t.topic_id
GROUP BY t.topic_id, t.name
HAVING COUNT(ct.chunk_id) > (
    SELECT AVG(topic_chunk_count)
    FROM (
        SELECT COUNT(*) AS topic_chunk_count
        FROM chunk_topics
        GROUP BY topic_id
    ) sub
)
ORDER BY chunk_count DESC;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 7: CTE
-- Cache hit rate per student
-- Purpose: Measure caching effectiveness across the user base
-- ─────────────────────────────────────────────────────────────────────
WITH student_query_stats AS (
    SELECT
        student_id,
        COUNT(*)                                    AS total_queries,
        COUNT(*) FILTER (WHERE was_cache_hit)       AS cache_hits
    FROM queries
    GROUP BY student_id
)
SELECT
    s.full_name,
    sqs.total_queries,
    sqs.cache_hits,
    ROUND(100.0 * sqs.cache_hits / sqs.total_queries, 1) AS hit_rate_pct
FROM student_query_stats sqs
JOIN students s ON s.student_id = sqs.student_id
ORDER BY hit_rate_pct DESC;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 8: CTE
-- Top-cited chunks: which source chunks are most frequently used
-- in answers, traced back to their source document
-- Purpose: Identify the most valuable content in the corpus
-- ─────────────────────────────────────────────────────────────────────
WITH citation_counts AS (
    SELECT
        chunk_id,
        COUNT(*)                       AS times_cited,
        ROUND(AVG(similarity_score)::numeric, 4) AS avg_similarity
    FROM solution_citations
    GROUP BY chunk_id
),
top_chunks AS (
    SELECT *
    FROM citation_counts
    ORDER BY times_cited DESC
    LIMIT 15
)
SELECT
    tc.chunk_id,
    tc.times_cited,
    tc.avg_similarity,
    d.title          AS source_document,
    d.course_code,
    LEFT(c.content, 100) AS chunk_preview
FROM top_chunks tc
JOIN chunks c             ON c.chunk_id = tc.chunk_id
JOIN document_versions dv ON dv.version_id = c.version_id
JOIN documents d          ON d.document_id = dv.document_id
ORDER BY tc.times_cited DESC;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 9: WINDOW FUNCTION
-- Rank students by total number of queries asked (dense rank)
-- Purpose: Leaderboard / engagement ranking
-- ─────────────────────────────────────────────────────────────────────
SELECT
    s.full_name,
    COUNT(q.query_id) AS total_queries,
    DENSE_RANK() OVER (ORDER BY COUNT(q.query_id) DESC) AS activity_rank
FROM students s
LEFT JOIN queries q ON q.student_id = s.student_id
GROUP BY s.student_id, s.full_name
ORDER BY activity_rank;


-- ─────────────────────────────────────────────────────────────────────
-- QUERY 10: WINDOW FUNCTION
-- Running average of feedback ratings over time (by day)
-- Purpose: Track answer quality trends over the semester
-- ─────────────────────────────────────────────────────────────────────
SELECT
    DATE(f.created_at)   AS feedback_date,
    f.rating             AS daily_rating,
    ROUND(
        AVG(f.rating) OVER (
            ORDER BY DATE(f.created_at)
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_7day_avg,
    COUNT(*) OVER (
        ORDER BY DATE(f.created_at)
    ) AS cumulative_feedback_count
FROM feedback f
ORDER BY feedback_date;


-- =====================================================================
-- End of queries.sql
-- =====================================================================
