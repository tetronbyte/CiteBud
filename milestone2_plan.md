# Milestone 2 Plan — Dataset & Queries

**Due:** 15 May 2026, 23:59 EAT
**Weight:** 20% of project (40 raw marks, scaled)

---

## Deliverables

| File | Purpose |
|------|---------|
| `data/` directory (CSVs or seed script) | Seed data for all 11 tables |
| `queries/queries.sql` | 10+ labelled SQL queries |
| `README.md` | Data dictionary + import instructions |

---

## Rubric

| Marks | Criterion | Evidence Required |
|-------|-----------|-------------------|
| 10 | Dataset Quality | Real or realistic; 1000+ rows; no junk data |
| 10 | Query Coverage | Min: 2 aggregations, 2 joins, 2 subqueries, 2 CTEs, 2 window functions |
| 10 | Query Correctness | All 10 queries run and return correct, meaningful results |
| 5 | Code Quality | Queries formatted, commented, named descriptively |
| 5 | README | Clear instructions to reproduce results from scratch |

---

## Dataset Plan

### Row Distribution (Target ~2900+ total, well above 1000 minimum)

| Table | Rows | Notes |
|-------|------|-------|
| `students` | ~20 | Fake students with realistic emails |
| `documents` | ~50 | Spread across students, various courses |
| `document_versions` | ~60 | Most docs 1 version, some have 2 |
| `chunks` | ~800+ | Bulk of rows — text chunks with 384-dim embeddings |
| `topics` | ~30 | Named academic topics (CS/Math/Physics etc.) |
| `chunk_topics` | ~1200 | M:N pairings, avg ~1.5 topics per chunk |
| `queries` | ~150 | Questions asked by students |
| `solutions` | ~100 | Fewer than queries (cache hits) |
| `solution_citations` | ~300 | ~3 citations per solution |
| `feedback` | ~80 | Not every query gets rated |
| `user_topic_profile` | ~100 | Student x topic confidence scores |

### Data Generation Strategy

- Python script (`data/seed_data.py`) generates all data
- Real 384-dim embeddings from `sentence-transformers` on realistic academic text
- Academic text sourced from realistic chunk content (CS, math, physics domains)
- Proper FK relationships maintained throughout
- Exports as SQL INSERT statements (`data/seed.sql`) for easy loading

---

## Queries Plan (queries.sql)

| # | Type | Query Idea |
|---|------|------------|
| 1 | Aggregation | Average feedback rating per difficulty level |
| 2 | Aggregation | Count of queries per student, grouped by month |
| 3 | Join | All queries with solution text and feedback rating |
| 4 | Join | Chunks with document title and topic names |
| 5 | Subquery | Students with above-average confidence scores |
| 6 | Subquery | Topics appearing in more chunks than the median |
| 7 | CTE | Cache hit rate per student |
| 8 | CTE | Top-cited chunks traced back to source documents |
| 9 | Window function | Rank students by total queries (RANK) |
| 10 | Window function | Running average of feedback rating over time (AVG OVER) |

---

## README Requirements

- [ ] Project description
- [ ] Data dictionary (every column: meaning, type, allowed values)
- [ ] Data source explanation (synthetic generation method documented)
- [ ] Exact import commands (schema.sql + seed.sql)
- [ ] Step-by-step "reproduce from zero" instructions
- [ ] AI usage disclosure

---

## Task Order

1. Write `data/seed_data.py` — generates realistic seed data
2. Run it to produce `data/seed.sql`
3. Write `queries/queries.sql` — 10 labelled queries
4. Update `README.md` — full data dictionary + repro steps
5. Test end-to-end: fresh DB, load schema, load data, run queries
