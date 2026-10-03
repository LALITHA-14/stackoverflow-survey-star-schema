WITH country_technology_counts AS (
    SELECT
        c.country_name AS country,
        TRIM(technology) AS technology,
        COUNT(*) AS developer_count
    FROM fact_responses f
    JOIN dim_country c
        ON c.country_id = f.country_id
    CROSS JOIN LATERAL unnest(
        string_to_array(f.LanguageHaveWorkedWith, ';')
    ) AS technology
    WHERE c.country_name IN (
        'United States of America',
        'India',
        'Germany',
        'United Kingdom of Great Britain and Northern Ireland'
    )
      AND f.LanguageHaveWorkedWith IS NOT NULL
      AND TRIM(technology) <> ''
    GROUP BY c.country_name, TRIM(technology)
),
ranked AS (
    SELECT
        country,
        technology,
        developer_count,
        ROW_NUMBER() OVER (
            PARTITION BY country
            ORDER BY developer_count DESC, technology
        ) AS technology_rank
    FROM country_technology_counts
)
SELECT
    country,
    technology,
    developer_count,
    technology_rank
FROM ranked
WHERE technology_rank <= 5
ORDER BY country, technology_rank;
