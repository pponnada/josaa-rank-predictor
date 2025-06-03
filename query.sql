WITH yearly_avg_rankings AS (
    SELECT
        r.year,
        r.college_id,
        r.academic_program_name_id,
        AVG(r.closing_rank) AS avg_closing_rank
    FROM
        rankings r
    WHERE
        r.gender = 'Gender-Neutral'
        AND r.seat_type = 'OPEN'
        AND r.quota IN ('AI', 'OS')
    GROUP BY
        r.year,
        r.college_id,
        r.academic_program_name_id
),
ranked_years AS (
    SELECT
        yar.year,
        yar.college_id,
        yar.academic_program_name_id,
        yar.avg_closing_rank,
        ROW_NUMBER() OVER (PARTITION BY yar.college_id, yar.academic_program_name_id ORDER BY yar.year ASC) AS year_rank
    FROM
        yearly_avg_rankings yar
)
SELECT
    r.year,
    r.round,
    r.opening_rank,
    r.closing_rank,
    MAX(r2.closing_rank) AS prev_year_closing_rank,
    r.closing_rank - MAX(r2.closing_rank) AS delta_closing_rank_1yr,
    r.closing_rank - (COALESCE(MAX(r2.closing_rank), 0) + COALESCE(MAX(r3.closing_rank), 0)) / 2.0 AS delta_closing_rank_2yr_avg,
       CASE
        WHEN r.round = (SELECT MAX(round) FROM rankings r2 
            WHERE r2.college_id = r.college_id 
            AND r2.academic_program_name_id = r.academic_program_name_id AND r2.year = r.year)
        THEN 1
        ELSE 0
    END AS is_final_round,
    r.closing_rank - (SELECT closing_rank FROM rankings r2 
        WHERE r2.college_id = r.college_id 
        AND r2.academic_program_name_id = r.academic_program_name_id 
        AND r2.year = r.year AND r2.round = r.round - 1) AS round_relative_rank_diff,
    CASE
        WHEN r.round = 1 THEN 0
        ELSE (r.closing_rank - (SELECT closing_rank FROM rankings r2 
            WHERE r2.college_id = r.college_id 
            AND r2.academic_program_name_id = r.academic_program_name_id 
            AND r2.year = r.year AND r2.round = 1)) * 100.0 / (SELECT closing_rank FROM rankings r2 
                WHERE r2.college_id = r.college_id 
                AND r2.academic_program_name_id = r.academic_program_name_id 
                AND r2.year = r.year AND r2.round = 1)
    END AS closing_rank_percent_change_from_round1,
        (
        SELECT AVG(yearly_avg)
        FROM (
            SELECT AVG(closing_rank) AS yearly_avg, year
            FROM rankings r4
            WHERE r4.college_id = r.college_id
            AND r4.academic_program_name_id = r.academic_program_name_id
            AND r4.gender = 'Gender-Neutral'
            AND r4.seat_type = 'OPEN'
            AND r4.quota IN ('AI', 'OS')
            AND r4.year IN (r.year, r.year - 1)
            GROUP BY year
            ORDER BY year DESC
            LIMIT 2
        ) AS last_2_years_avg
    ) AS mean_closing_rank_last_2yrs,
    CASE
        WHEN ry.year_rank = 1 THEN NULL
        WHEN ry.year_rank = 2 THEN (SELECT avg_closing_rank FROM yearly_avg_rankings yar2 WHERE yar2.college_id = r.college_id AND yar2.academic_program_name_id = r.academic_program_name_id AND yar2.year = r.year - 1)
        ELSE 0.6 * (SELECT avg_closing_rank FROM yearly_avg_rankings yar2 WHERE yar2.college_id = r.college_id AND yar2.academic_program_name_id = r.academic_program_name_id AND yar2.year = r.year - 1) +
             0.4 * (SELECT avg_closing_rank FROM yearly_avg_rankings yar2 WHERE yar2.college_id = r.college_id AND yar2.academic_program_name_id = r.academic_program_name_id AND yar2.year = r.year - 2)
    END AS weighted_moving_avg,
    c.name AS college_name,
    apn.name AS academic_program_name
FROM
    rankings r
LEFT JOIN colleges c ON r.college_id = c.id
LEFT JOIN academic_program_name apn ON r.academic_program_name_id = apn.id
LEFT JOIN rankings r2 ON r.college_id = r2.college_id 
    AND r.academic_program_name_id = r2.academic_program_name_id 
    AND r.year = r2.year + 1 
    AND r2.gender = 'Gender-Neutral' 
    AND r2.seat_type = 'OPEN' 
    AND r2.quota IN ('AI', 'OS')
LEFT JOIN rankings r3 ON r.college_id = r3.college_id 
    AND r.academic_program_name_id = r3.academic_program_name_id 
    AND r.year = r3.year + 2 
    AND r3.gender = 'Gender-Neutral' 
    AND r3.seat_type = 'OPEN' 
    AND r3.quota IN ('AI', 'OS')
LEFT JOIN ranked_years ry ON r.college_id = ry.college_id AND r.academic_program_name_id = ry.academic_program_name_id AND r.year = ry.year
WHERE
    r.gender = 'Gender-Neutral'
    AND r.seat_type = 'OPEN'
    AND r.quota IN ('AI', 'OS')
    AND c.name NOT LIKE '%Indian Institute of Technology%'
GROUP BY r.year, r.round, r.opening_rank, r.closing_rank, c.name, apn.name
ORDER BY
    c.name ASC,
    apn.name ASC,
    r.year ASC,
    r.round ASC;
