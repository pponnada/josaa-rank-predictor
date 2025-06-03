import sqlite3
import csv
import os
from pathlib import Path
import re # For parsing round number from filename

# --- Configuration ---
DB_FILENAME = "josaa.db"
TABLE_NAME = "josaa_rankings"

# Original CSV headers (order matters for direct mapping)
CSV_HEADERS_FROM_FILE = [
    "Institute", "Academic Program Name", "Quota", "Seat Type",
    "Gender", "Opening Rank", "Closing Rank"
]

# Corresponding SQLite column names for CSV data
SQLITE_COLUMNS_FOR_CSV_DATA = [
    "institute", "academic_program_name", "quota", "seat_type",
    "gender", "opening_rank", "closing_rank"
]

def sanitize_header_for_sqlite(header_name):
    """Converts CSV header to a SQLite-friendly column name."""
    return header_name.lower().replace(' ', '_').replace('-', '_').replace('.', '')

def create_db_and_table(db_path):
    """Creates the SQLite database and the table if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build column definitions dynamically from CSV_HEADERS_FROM_FILE
    column_definitions_from_csv = []
    for header in CSV_HEADERS_FROM_FILE:
        col_name = sanitize_header_for_sqlite(header)
        if "rank" in col_name: # A bit simplistic, but works for "Opening Rank", "Closing Rank"
            col_type = "REAL"
        else:
            col_type = "TEXT"
        column_definitions_from_csv.append(f"{col_name} {col_type}")

    # Add year and round columns with correct types
    dynamic_column_definitions = column_definitions_from_csv + [
        "year INTEGER",
        "round INTEGER" # Changed to INTEGER
    ]

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {', '.join(dynamic_column_definitions)}
    );
    """

    print(f"Creating database table with SQL: {create_table_sql}")
    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()
    print(f"Database '{db_path}' checked/created with table '{TABLE_NAME}'.")

def process_csv_file(db_conn, csv_filepath, year, round_number_int): # round_number_int is now an integer
    """Reads a CSV file and inserts its data into the database."""
    cursor = db_conn.cursor()
    
    # Construct the INSERT SQL statement dynamically
    # Ensure the order matches SQLITE_COLUMNS_FOR_CSV_DATA + year + round
    db_columns_for_insert = SQLITE_COLUMNS_FOR_CSV_DATA + ["year", "round"]
    placeholders = ', '.join(['?'] * len(db_columns_for_insert))
    
    insert_sql = f"""
    INSERT INTO {TABLE_NAME} (
        {', '.join(db_columns_for_insert)}
    ) VALUES ({placeholders});
    """

    rows_processed = 0
    rows_skipped = 0

    try:
        with open(csv_filepath, 'r', encoding='utf-8', errors='replace') as file: # Added errors='replace' for robustness
            reader = csv.reader(file, delimiter='#')
            
            try:
                header_row_from_file = next(reader)  # Read header row
            except StopIteration:
                print(f"Skipping empty CSV file: {csv_filepath}")
                return

            # Optional: Validate header (compare sanitized version with SQLITE_COLUMNS_FOR_CSV_DATA)
            sanitized_header_from_file = [sanitize_header_for_sqlite(h) for h in header_row_from_file]
            # This check assumes CSV_HEADERS_FROM_FILE reflects the *expected* columns we care about.
            # If a CSV has more columns, we'll only take the ones defined in CSV_HEADERS_FROM_FILE.
            # If it has fewer, an IndexError might occur later, which is handled.

            for i, row in enumerate(reader):
                # Handle empty or malformed rows
                if len(row) < len(CSV_HEADERS_FROM_FILE) or not any(field.strip() for field in row[:len(CSV_HEADERS_FROM_FILE)]):
                    # print(f"Skipping empty or malformed row {i+2} in {csv_filepath}: {row}")
                    rows_skipped +=1
                    continue

                try:
                    # Prepare data for insertion based on CSV_HEADERS_FROM_FILE
                    data_to_insert = []
                    for idx, header_name in enumerate(CSV_HEADERS_FROM_FILE):
                        value = row[idx].strip() # Get value by index from the row
                        if header_name in ["Opening Rank", "Closing Rank"]:
                            if value == "Gender-Neutral":
                                data_to_insert.append(-1)
                            else:
                                data_to_insert.append(float(value) if value else None)
                        else:
                            data_to_insert.append(value)

                    # Add year and round (integer)
                    data_to_insert.extend([year, round_number_int])

                    # Check for empty values (just spaces)
                    if any(val == " " for val in data_to_insert):
                        print(f"Skipping row {i+2} in {csv_filepath}: Contains empty values (just spaces).")
                        rows_skipped += 1
                        continue

                    # Check if the number of values matches the expected number of columns
                    expected_column_count = len(SQLITE_COLUMNS_FOR_CSV_DATA) + 2  # +2 for year and round
                    if len(data_to_insert) != expected_column_count:
                        print(f"Skipping row {i+2} in {csv_filepath}: Incorrect number of columns (expected {expected_column_count}, got {len(data_to_insert)}).")
                        rows_skipped += 1
                        continue

                    cursor.execute(insert_sql, tuple(data_to_insert))
                    rows_processed += 1
                except ValueError as ve:
                    print(f"ValueError processing row {i+2} (0-indexed data) in {csv_filepath}: {row} - {ve}. Skipping.")
                    rows_skipped += 1
                except IndexError as ie:
                    print(f"IndexError (likely missing columns) processing row {i+2} (0-indexed data) in {csv_filepath}: {row} - {ie}. Skipping.")
                    rows_skipped += 1

        db_conn.commit()
        if rows_processed > 0 or rows_skipped > 0:
            print(f"  Processed {csv_filepath.name}: Inserted {rows_processed} rows, Skipped {rows_skipped} rows.")

    except FileNotFoundError:
        print(f"Error: File not found {csv_filepath}")
    except Exception as e:
        print(f"An error occurred while processing {csv_filepath}: {e}")


def main(base_directory_str):
    """Main function to orchestrate database creation and data population."""
    base_dir = Path(base_directory_str)
    db_path = base_dir / DB_FILENAME # Place DB in the base directory itself

    create_db_and_table(db_path)

    conn = sqlite3.connect(db_path)

    for item_in_base in base_dir.iterdir():
        if item_in_base.is_dir() and item_in_base.name.isdigit() and len(item_in_base.name) == 4:
            try:
                year = int(item_in_base.name)
            except ValueError:
                # This case should ideally not be hit due to the isdigit() check, but defensive.
                print(f"Skipping directory '{item_in_base.name}' as it's not a valid year format.")
                continue
            
            print(f"\nProcessing year directory: {year}")
            for csv_file_path in item_in_base.glob('*.psv'):
                filename_stem = csv_file_path.stem  # e.g., "round1"
                
                # Extract round number from filename using regex
                match = re.match(r"round(\d+)", filename_stem, re.IGNORECASE)
                if match:
                    try:
                        round_num_int = int(match.group(1))
                        # print(f"  Found CSV: {csv_file_path.name}, Year: {year}, Round: {round_num_int}")
                        process_csv_file(conn, csv_file_path, year, round_num_int)
                    except ValueError:
                        print(f"  Could not parse round number as integer from '{match.group(1)}' in {csv_file_path.name}. Skipping.")
                else:
                    print(f"  Filename '{csv_file_path.name}' does not match 'round<number>.csv' pattern. Skipping.")
    
    conn.close()
    print(f"\nFinished processing. Database '{db_path}' is populated.")

if __name__ == "__main__":
    main(".")
