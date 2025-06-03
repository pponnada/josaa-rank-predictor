CREATE TABLE IF NOT EXISTS josaa_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institute TEXT,
    academic_program_name TEXT,
    quota TEXT,
    seat_type TEXT,
    gender TEXT,
    opening_rank INTEGER,
    closing_rank INTEGER,
    year INTEGER,
    round INTEGER 
);