SELECT
    f.response_id,
    c.country_name AS country,
    d.dev_type_name AS dev_type,
    f.ConvertedCompYearly AS salary,
    AVG(f.ConvertedCompYearly) OVER (
        PARTITION BY c.country_name, d.dev_type_name
    ) AS average_peer_salary
FROM fact_responses f
JOIN dim_country c
    ON c.country_id = f.country_id
JOIN dim_developer_type d
    ON d.dev_type_id = f.dev_type_id
WHERE f.ConvertedCompYearly IS NOT NULL
ORDER BY country, dev_type, response_id;
