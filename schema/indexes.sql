CREATE INDEX IF NOT EXISTS idx_fact_responses_country_id
    ON fact_responses (country_id);

CREATE INDEX IF NOT EXISTS idx_fact_responses_employment_id
    ON fact_responses (employment_id);

CREATE INDEX IF NOT EXISTS idx_fact_responses_dev_type_id
    ON fact_responses (dev_type_id);

CREATE INDEX IF NOT EXISTS idx_fact_responses_converted_comp_yearly
    ON fact_responses (ConvertedCompYearly);