DROP TABLE IF EXISTS fact_responses CASCADE;
DROP TABLE IF EXISTS dim_country CASCADE;
DROP TABLE IF EXISTS dim_employment CASCADE;
DROP TABLE IF EXISTS dim_developer_type CASCADE;

CREATE TABLE dim_country (
    country_id SERIAL PRIMARY KEY,
    country_name TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_employment (
    employment_id SERIAL PRIMARY KEY,
    employment_name TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_developer_type (
    dev_type_id SERIAL PRIMARY KEY,
    dev_type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_responses (
    response_id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES dim_country(country_id),
    employment_id INTEGER NOT NULL REFERENCES dim_employment(employment_id),
    dev_type_id INTEGER NOT NULL REFERENCES dim_developer_type(dev_type_id),
    ConvertedCompYearly NUMERIC(18, 2),
    YearsCode INTEGER,
    LanguageHaveWorkedWith TEXT,
    LanguageWantToWorkWith TEXT
);