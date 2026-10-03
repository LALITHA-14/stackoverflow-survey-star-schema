WITH salary_data AS (
    SELECT
        f.response_id,
        c.country_name AS country,
        f.ConvertedCompYearly AS salary
    FROM fact_responses f
    JOIN dim_country c
        ON c.country_id = f.country_id
    WHERE f.ConvertedCompYearly IS NOT NULL
)
SELECT
    response_id,
    country,
    salary,
    NTILE(100) OVER (
        PARTITION BY country
        ORDER BY salary
    ) AS salary_percentile
FROM salary_data
ORDER BY country, salary, response_id;
