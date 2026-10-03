WITH salary_data AS (
    SELECT
        f.response_id,
        f.YearsCode AS years_of_experience,
        c.country_name AS country,
        f.ConvertedCompYearly AS salary
    FROM fact_responses f
    JOIN dim_country c
        ON c.country_id = f.country_id
    WHERE f.ConvertedCompYearly IS NOT NULL
      AND f.YearsCode IS NOT NULL
)
SELECT
    response_id,
    years_of_experience,
    country,
    salary,
    RANK() OVER (
        PARTITION BY years_of_experience
        ORDER BY salary DESC
    ) AS compensation_rank
FROM salary_data
ORDER BY years_of_experience, compensation_rank, response_id;
