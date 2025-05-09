# Class Scheduling Database - Phase II - Task 2
The ETL process reads class scheduling data from an Excel file, transforms it according to the database schema, and loads it into a SQLite database. The database includes information about departments, courses, terms, instructors, sections, buildings, and schedules.

## Files in this Repository

- `README.md` - Project documentation and setup instructions
- `requirements.txt` - Python dependencies required for the project
- `etl_process.py` - Python implementation of the ETL process
- `validation.sql` - SQL queries to validate the database contents
- `sample ClassSched-CS-S25.xlsx` - Sample class scheduling data file

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # OR
   .\venv\Scripts\activate  # On Windows
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the ETL Process

1. Run the ETL script:

   ```bash
   python etl_process.py
   ```

   This will:

   - Create a new SQLite database (`class_schedule.db`)
   - Read data from the Excel file
   - Transform and load the data into the database
   - Validate the loaded data

2. Validate the database:
   ```bash
   sqlite3 class_schedule.db < validation.sql > validation_results.txt
   ```
   This will run validation queries and save the results to `validation_results.txt`

## Database Schema

The database includes the following tables:

- `department` - Department information
- `course` - Course details
- `term` - Academic terms
- `instructor` - Instructor information
- `section` - Course sections
- `building` - Building information
- `schedule` - Class schedules

## Author

Chantelle Cabanilla

## Date

05/09/2025
