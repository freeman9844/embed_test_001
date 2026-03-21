-- 예시설계: 단일 SQL 쿼리로 구사하는 Server-Side RRF (Reciprocal Rank Fusion)
WITH visual_ranks AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) as rank
    FROM video_scenes_v4
    WHERE id != 'init'
    LIMIT 10
),
text_ranks AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY text_embedding <=> $2::vector) as rank
    FROM video_scenes_v4
    WHERE id != 'init'
    LIMIT 10
),
fts_ranks AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(to_tsvector('simple', description), plainto_tsquery('simple', $3)) DESC) as rank
    FROM video_scenes_v4
    WHERE id != 'init' AND to_tsvector('simple', description) @@ plainto_tsquery('simple', $3)
    LIMIT 10
)
SELECT 
    v.id,
    v.segment_index,
    v.start_time,
    v.end_time,
    v.video_name,
    v.description,
    v.url,
    -- RRF 점수 계산: (1 / (Rank_V + 60)) + (1 / (Rank_T + 60)) + (1 / (Rank_F + 60))
    COALESCE(1.0 / (vr.rank + 60), 0) + 
    COALESCE(1.0 / (tr.rank + 60), 0) + 
    COALESCE(1.0 / (fr.rank + 60), 0) AS rrf_score
FROM video_scenes_v4 v
LEFT JOIN visual_ranks vr ON v.id = vr.id
LEFT JOIN text_ranks tr ON v.id = tr.id
LEFT JOIN fts_ranks fr ON v.id = fr.id
WHERE vr.id IS NOT NULL OR tr.id IS NOT NULL OR fr.id IS NOT NULL
ORDER BY rrf_score DESC
LIMIT 10;
