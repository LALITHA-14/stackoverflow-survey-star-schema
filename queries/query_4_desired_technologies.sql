WITH python_users AS (
    SELECT
        f.response_id,
        f.LanguageWantToWorkWith
    FROM fact_responses f
    WHERE f.LanguageHaveWorkedWith IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM unnest(string_to_array(f.LanguageHaveWorkedWith, ';')) AS lang
          WHERE TRIM(lang) = 'Python'
      )
),
desired_counts AS (
    SELECT
        TRIM(desired_language) AS technology,
        COUNT(*) AS developer_count
    FROM python_users p
    CROSS JOIN LATERAL unnest(
        string_to_array(p.LanguageWantToWorkWith, ';')
    ) AS desired_language
    WHERE p.LanguageWantToWorkWith IS NOT NULL
      AND TRIM(desired_language) <> ''
    GROUP BY TRIM(desired_language)
),
ranked AS (
    SELECT
        technology,
        developer_count,
        ROW_NUMBER() OVER (
            ORDER BY developer_count DESC, technology
        ) AS technology_rank
    FROM desired_counts
)
SELECT
    technology,
    developer_count,
    technology_rank
FROM ranked
WHERE technology_rank <= 3
ORDER BY technology_rank;
