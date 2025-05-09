"""
ETL Process for Class Scheduling Database

This script performs the Extract-Transform-Load (ETL) process for the Class Scheduling Database.
It reads data from an Excel file, transforms it according to the database schema, and loads it
into a SQLite database.

Author: Chantelle Cabanilla
Date: 05/09/2025
"""

import pandas as pd
import sqlite3
import os
import re
from datetime import datetime

# Configure file paths
EXCEL_FILE = 'sample ClassSched-CS-S25.xlsx'
DB_FILE = 'class_schedule.db'

# Remove existing database if it exists
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"Removed existing database: {DB_FILE}")

# Connect to SQLite database
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
print(f"Connected to database: {DB_FILE}")

def create_database_schema():
    """
    Create the database schema based on the ERD.
    """
    print("Creating database schema...")
    
    # Department table
    cursor.execute('''
    CREATE TABLE department (
        dept_id INTEGER PRIMARY KEY,
        dept_code TEXT NOT NULL,
        dept_name TEXT NOT NULL
    )
    ''')
    
    # Course table
    cursor.execute('''
    CREATE TABLE course (
        course_id INTEGER PRIMARY KEY,
        dept_id INTEGER NOT NULL,
        course_num TEXT NOT NULL,
        course_name TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES department(dept_id)
    )
    ''')
    
    # Term table
    cursor.execute('''
    CREATE TABLE term (
        term_id INTEGER PRIMARY KEY,
        term_code TEXT NOT NULL,
        term_name TEXT NOT NULL,
        start_date TEXT NOT NULL
    )
    ''')
    
    # Instructor table
    cursor.execute('''
    CREATE TABLE instructor (
        instr_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT
    )
    ''')
    
    # Section table
    cursor.execute('''
    CREATE TABLE section (
        section_id INTEGER PRIMARY KEY,
        course_id INTEGER NOT NULL,
        term_id INTEGER NOT NULL,
        instr_id INTEGER NOT NULL,
        section_num TEXT NOT NULL,
        max_seats INTEGER NOT NULL,
        FOREIGN KEY (course_id) REFERENCES course(course_id),
        FOREIGN KEY (term_id) REFERENCES term(term_id),
        FOREIGN KEY (instr_id) REFERENCES instructor(instr_id)
    )
    ''')
    
    # Building table
    cursor.execute('''
    CREATE TABLE building (
        bldg_id INTEGER PRIMARY KEY,
        bldg_code TEXT NOT NULL,
        bldg_name TEXT NOT NULL
    )
    ''')
    
    # Schedule table
    cursor.execute('''
    CREATE TABLE schedule (
        schedule_id INTEGER PRIMARY KEY,
        section_id INTEGER NOT NULL,
        bldg_id INTEGER NOT NULL,
        room_num TEXT NOT NULL,
        day_pattern TEXT NOT NULL,
        FOREIGN KEY (section_id) REFERENCES section(section_id),
        FOREIGN KEY (bldg_id) REFERENCES building(bldg_id)
    )
    ''')
    
    # Commit the changes
    conn.commit()
    print("Database schema created successfully")

def read_excel_data():
    """
    Read the Excel file and return a pandas DataFrame.
    """
    print(f"Reading Excel file: {EXCEL_FILE}")
    
    # Read Excel file, skipping the first row (title)
    df = pd.read_excel(EXCEL_FILE, skiprows=1)
    
    # Clean column names (remove spaces and special chars)
    df.columns = [col.strip() for col in df.columns]
    
    print(f"Read {len(df)} rows from Excel file")
    return df

def process_departments(df):
    """
    Process department data from the DataFrame and load into the database.
    Returns a dictionary mapping department keys to dept_id values.
    """
    print("Processing department data...")
    
    # Extract unique departments
    departments = df[['College', 'Acad Org']].drop_duplicates()
    
    # Create department data
    dept_data = []
    for idx, (_, row) in enumerate(departments.iterrows(), 1):
        dept_data.append({
            'dept_id': idx,
            'dept_code': row['Acad Org'],
            'dept_name': row['College']
        })
    
    # Insert departments into the database
    for dept in dept_data:
        cursor.execute('''
        INSERT INTO department (dept_id, dept_code, dept_name)
        VALUES (?, ?, ?)
        ''', (dept['dept_id'], dept['dept_code'], dept['dept_name']))
    
    # Create a lookup dictionary for department IDs
    dept_lookup = {f"{dept['dept_code']}_{dept['dept_name']}": dept['dept_id'] for dept in dept_data}
    
    conn.commit()
    print(f"Processed {len(dept_data)} departments")
    return dept_lookup

def process_courses(df, dept_lookup):
    """
    Process course data from the DataFrame and load into the database.
    Returns a dictionary mapping course keys to course_id values.
    """
    print("Processing course data...")
    
    # Extract unique courses
    df['SubjectCatalog'] = df['Subject'] + df['Catalog'].astype(str)
    courses = df[['SubjectCatalog', 'Title', 'College', 'Acad Org']].drop_duplicates()
    
    # Create course data
    course_data = []
    for idx, (_, row) in enumerate(courses.iterrows(), 1):
        dept_key = f"{row['Acad Org']}_{row['College']}"
        dept_id = dept_lookup.get(dept_key)
        
        course_data.append({
            'course_id': idx,
            'dept_id': dept_id,
            'course_num': row['SubjectCatalog'],
            'course_name': row['Title']
        })
    
    # Insert courses into the database
    for course in course_data:
        cursor.execute('''
        INSERT INTO course (course_id, dept_id, course_num, course_name)
        VALUES (?, ?, ?, ?)
        ''', (course['course_id'], course['dept_id'], course['course_num'], course['course_name']))
    
    # Create a lookup dictionary for course IDs
    course_lookup = {f"{course['course_num']}_{course['course_name']}": course['course_id'] for course in course_data}
    
    conn.commit()
    print(f"Processed {len(course_data)} courses")
    return course_lookup

def process_terms(df):
    """
    Process term data from the DataFrame and load into the database.
    Returns a dictionary mapping term dates to term_id values.
    """
    print("Processing term data...")
    
    # Extract unique terms
    df['TermKey'] = df['Start Date'].astype(str) + '_' + df['End Date'].astype(str)
    terms = df[['TermKey', 'Start Date', 'End Date']].drop_duplicates()
    
    # Create term data
    term_data = []
    for idx, (_, row) in enumerate(terms.iterrows(), 1):
        # Parse the date string
        start_date = row['Start Date']
        end_date = row['End Date']
        
        # Format the term code and name
        if isinstance(start_date, str):
            # Parse the date string if it's a string
            try:
                start_date_obj = datetime.strptime(start_date, '%m/%d/%y')
                end_date_obj = datetime.strptime(end_date, '%m/%d/%y')
                term_code = f"{start_date_obj.year}{start_date_obj.month:02d}"
                term_name = f"{start_date_obj.strftime('%b %Y')} - {end_date_obj.strftime('%b %Y')}"
            except ValueError:
                # Default values if date parsing fails
                term_code = f"TERM{idx}"
                term_name = f"Term {idx}"
        else:
            # If start_date is already a datetime object
            try:
                term_code = f"{start_date.year}{start_date.month:02d}"
                term_name = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
            except AttributeError:
                # Handle case where date isn't a datetime object
                term_code = f"TERM{idx}"
                term_name = f"Term {idx}"
        
        term_data.append({
            'term_id': idx,
            'term_code': term_code,
            'term_name': term_name,
            'start_date': str(start_date)  # Store as string
        })
    
    # Insert terms into the database
    for term in term_data:
        cursor.execute('''
        INSERT INTO term (term_id, term_code, term_name, start_date)
        VALUES (?, ?, ?, ?)
        ''', (term['term_id'], term['term_code'], term['term_name'], term['start_date']))
    
    # Create a lookup dictionary for term IDs
    term_lookup = {term['start_date']: term['term_id'] for term in term_data}
    
    conn.commit()
    print(f"Processed {len(term_data)} terms")
    return term_lookup

def process_instructors(df):
    """
    Process instructor data from the DataFrame and load into the database.
    Returns a dictionary mapping instructor names to instr_id values.
    """
    print("Processing instructor data...")
    
    # Extract unique instructors
    instructors = df[['Instructor First Name', 'Instructor Last Name']].drop_duplicates()
    
    # Create instructor data
    instructor_data = []
    for idx, (_, row) in enumerate(instructors.iterrows(), 1):
        first_name = row['Instructor First Name']
        last_name = row['Instructor Last Name']
        
        # Generate email (placeholder)
        if pd.notna(first_name) and pd.notna(last_name):
            email = f"{first_name.lower()}.{last_name.lower()}@university.edu"
        else:
            email = "unknown@university.edu"
        
        instructor_data.append({
            'instr_id': idx,
            'first_name': first_name if pd.notna(first_name) else "Unknown",
            'last_name': last_name if pd.notna(last_name) else "Unknown",
            'email': email
        })
    
    # Insert instructors into the database
    for instr in instructor_data:
        cursor.execute('''
        INSERT INTO instructor (instr_id, first_name, last_name, email)
        VALUES (?, ?, ?, ?)
        ''', (instr['instr_id'], instr['first_name'], instr['last_name'], instr['email']))
    
    # Create a lookup dictionary for instructor IDs
    instr_lookup = {f"{instr['first_name']}_{instr['last_name']}": instr['instr_id'] for instr in instructor_data}
    
    conn.commit()
    print(f"Processed {len(instructor_data)} instructors")
    return instr_lookup

def process_buildings(df):
    """
    Process building data from the DataFrame and load into the database.
    Returns a dictionary mapping building codes to bldg_id values.
    """
    print("Processing building data...")
    
    # Function to extract building code from room
    def extract_building(room):
        if pd.isna(room):
            return "UNKNOWN"
        
        # Extract building code (assuming format like "SEM 101" where "SEM" is the building code)
        match = re.match(r'([A-Za-z]+)', room)
        if match:
            return match.group(1)
        else:
            return "UNKNOWN"
    
    # Extract building codes from Room column
    df['BuildingCode'] = df['Room'].apply(extract_building)
    buildings = df[['BuildingCode']].drop_duplicates()
    
    # Create building data
    building_data = []
    for idx, (_, row) in enumerate(buildings.iterrows(), 1):
        bldg_code = row['BuildingCode']
        
        # Generate building name based on code
        if bldg_code == "SEM":
            bldg_name = "Seminar Building"
        elif bldg_code == "WPEB":
            bldg_name = "William Pearson Engineering Building"
        else:
            bldg_name = f"{bldg_code} Building"
        
        building_data.append({
            'bldg_id': idx,
            'bldg_code': bldg_code,
            'bldg_name': bldg_name
        })
    
    # Insert buildings into the database
    for bldg in building_data:
        cursor.execute('''
        INSERT INTO building (bldg_id, bldg_code, bldg_name)
        VALUES (?, ?, ?)
        ''', (bldg['bldg_id'], bldg['bldg_code'], bldg['bldg_name']))
    
    # Create a lookup dictionary for building IDs
    bldg_lookup = {bldg['bldg_code']: bldg['bldg_id'] for bldg in building_data}
    
    conn.commit()
    print(f"Processed {len(building_data)} buildings")
    return bldg_lookup

def process_sections(df, course_lookup, term_lookup, instr_lookup):
    """
    Process section data from the DataFrame and load into the database.
    Returns a dictionary mapping section IDs to section_id values.
    """
    print("Processing section data...")
    
    # Using 'Class Nbr' as the section_id
    sections = df[['Class Nbr', 'Subject', 'Catalog', 'Title', 'Section', 'Start Date', 
                   'Instructor First Name', 'Instructor Last Name', 'Enrollment Capacity']].drop_duplicates()
    
    # Create section data
    section_data = []
    seen_class_nbrs = set()  # Keep track of used class numbers
    
    for _, row in sections.iterrows():
        class_nbr = row['Class Nbr']
        # If we've seen this class number before, skip it
        if class_nbr in seen_class_nbrs:
            print(f"Warning: Duplicate Class Nbr {class_nbr} found, skipping...")
            continue
            
        seen_class_nbrs.add(class_nbr)
        subject_catalog = row['Subject'] + str(row['Catalog'])
        course_key = f"{subject_catalog}_{row['Title']}"
        course_id = course_lookup.get(course_key)
        
        # Get term_id
        start_date = str(row['Start Date'])
        term_id = term_lookup.get(start_date)
        
        # Get instructor_id
        first_name = row['Instructor First Name'] if pd.notna(row['Instructor First Name']) else "Unknown"
        last_name = row['Instructor Last Name'] if pd.notna(row['Instructor Last Name']) else "Unknown"
        instr_key = f"{first_name}_{last_name}"
        instr_id = instr_lookup.get(instr_key)
        
        # Get enrollment capacity
        max_seats = row['Enrollment Capacity'] if pd.notna(row['Enrollment Capacity']) else 0
        
        section_data.append({
            'section_id': class_nbr,  # Use Class Nbr as section_id
            'course_id': course_id,
            'term_id': term_id,
            'instr_id': instr_id,
            'section_num': row['Section'],
            'max_seats': max_seats
        })
    
    # Insert sections into the database
    for section in section_data:
        cursor.execute('''
        INSERT INTO section (section_id, course_id, term_id, instr_id, section_num, max_seats)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (section['section_id'], section['course_id'], section['term_id'], 
              section['instr_id'], section['section_num'], section['max_seats']))
    
    # Create a lookup dictionary for section IDs
    section_lookup = {section['section_id']: section['section_id'] for section in section_data}
    
    conn.commit()
    print(f"Processed {len(section_data)} sections")
    return section_lookup

def process_schedules(df, section_lookup, bldg_lookup):
    """
    Process schedule data from the DataFrame and load into the database.
    """
    print("Processing schedule data...")
    
    # Extract schedule information
    schedules = df[['Class Nbr', 'Room', 'Class Days', 'Class Start Time', 'Class End Time']].drop_duplicates()
    
    # Function to extract room number
    def extract_room_number(room):
        if pd.isna(room):
            return "UNKNOWN"
        
        # Extract room number (assuming format like "SEM 101" where "101" is the room number)
        match = re.search(r'(\d+)$', room)
        if match:
            return match.group(1)
        else:
            return "UNKNOWN"
    
    # Create schedule data
    schedule_data = []
    for idx, (_, row) in enumerate(schedules.iterrows(), 1):
        class_nbr = row['Class Nbr']
        section_id = section_lookup.get(class_nbr)
        
        # Extract building code and room number
        if pd.notna(row['Room']):
            building_code = re.match(r'([A-Za-z]+)', row['Room'])
            building_code = building_code.group(1) if building_code else "UNKNOWN"
            room_num = extract_room_number(row['Room'])
        else:
            building_code = "UNKNOWN"
            room_num = "UNKNOWN"
        
        bldg_id = bldg_lookup.get(building_code)
        
        # Create day pattern
        day_pattern = ""
        if pd.notna(row['Class Days']):
            day_pattern += str(row['Class Days'])
        
        if pd.notna(row['Class Start Time']) and pd.notna(row['Class End Time']):
            day_pattern += f" {row['Class Start Time']}-{row['Class End Time']}"
        
        schedule_data.append({
            'schedule_id': idx,
            'section_id': section_id,
            'bldg_id': bldg_id,
            'room_num': room_num,
            'day_pattern': day_pattern
        })
    
    # Insert schedules into the database
    for schedule in schedule_data:
        cursor.execute('''
        INSERT INTO schedule (schedule_id, section_id, bldg_id, room_num, day_pattern)
        VALUES (?, ?, ?, ?, ?)
        ''', (schedule['schedule_id'], schedule['section_id'], 
              schedule['bldg_id'], schedule['room_num'], schedule['day_pattern']))
    
    conn.commit()
    print(f"Processed {len(schedule_data)} schedules")

def validate_database():
    """
    Run validation queries on the database to confirm its structure and contents.
    """
    print("\n--- Validating Database ---")
    
    # Count records in each table
    cursor.execute('''
    SELECT 'Department' as Table_Name, COUNT(*) as Record_Count FROM department
    UNION ALL
    SELECT 'Course', COUNT(*) FROM course
    UNION ALL
    SELECT 'Term', COUNT(*) FROM term
    UNION ALL
    SELECT 'Instructor', COUNT(*) FROM instructor
    UNION ALL
    SELECT 'Section', COUNT(*) FROM section
    UNION ALL
    SELECT 'Building', COUNT(*) FROM building
    UNION ALL
    SELECT 'Schedule', COUNT(*) FROM schedule;
    ''')
    
    results = cursor.fetchall()
    for table, count in results:
        print(f"{table}: {count} records")
    
    # Validate foreign key relationships
    print("\n--- Validating Foreign Key Relationships ---")
    
    # Courses per department
    cursor.execute('''
    SELECT d.dept_name, COUNT(c.course_id) as Course_Count
    FROM department d
    LEFT JOIN course c ON d.dept_id = c.dept_id
    GROUP BY d.dept_name
    ''')
    
    results = cursor.fetchall()
    print("Courses per Department:")
    for dept, count in results:
        print(f"{dept}: {count} courses")
    
    # Sections per course
    cursor.execute('''
    SELECT c.course_name, COUNT(s.section_id) as Section_Count
    FROM course c
    LEFT JOIN section s ON c.course_id = s.course_id
    GROUP BY c.course_name
    LIMIT 5
    ''')
    
    results = cursor.fetchall()
    print("\nSections per Course (top 5):")
    for course, count in results:
        print(f"{course}: {count} sections")
    
    # Teaching load per instructor
    cursor.execute('''
    SELECT i.last_name, i.first_name, COUNT(s.section_id) as Section_Count
    FROM instructor i
    LEFT JOIN section s ON i.instr_id = s.instr_id
    GROUP BY i.last_name, i.first_name
    LIMIT 5
    ''')
    
    results = cursor.fetchall()
    print("\nSections per Instructor (top 5):")
    for last_name, first_name, count in results:
        print(f"{first_name} {last_name}: {count} sections")
    
    # Complex query to show complete class schedule (sample)
    cursor.execute('''
    SELECT 
        d.dept_name as Department,
        c.course_num as Course,
        c.course_name as Title,
        s.section_num as Section,
        i.last_name as Instructor,
        t.term_name as Term,
        b.bldg_name as Building,
        sch.room_num as Room,
        sch.day_pattern as Schedule
    FROM schedule sch
    JOIN section s ON sch.section_id = s.section_id
    JOIN course c ON s.course_id = c.course_id
    JOIN department d ON c.dept_id = d.dept_id
    JOIN instructor i ON s.instr_id = i.instr_id
    JOIN term t ON s.term_id = t.term_id
    JOIN building b ON sch.bldg_id = b.bldg_id
    LIMIT 5
    ''')
    
    results = cursor.fetchall()
    print("\nSample Class Schedule (5 entries):")
    for row in results:
        print(f"{row[0]} - {row[1]} {row[2]} (Section {row[3]})")
        print(f"  Instructor: {row[4]}, Term: {row[5]}")
        print(f"  Location: {row[6]} Room {row[7]}, Schedule: {row[8]}")
        print()

def main():
    """
    Main ETL process function.
    """
    print("Starting ETL process...")
    
    # Create database schema
    create_database_schema()
    
    # Read Excel data
    df = read_excel_data()
    
    # Process data for each table
    dept_lookup = process_departments(df)
    course_lookup = process_courses(df, dept_lookup)
    term_lookup = process_terms(df)
    instr_lookup = process_instructors(df)
    bldg_lookup = process_buildings(df)
    section_lookup = process_sections(df, course_lookup, term_lookup, instr_lookup)
    process_schedules(df, section_lookup, bldg_lookup)
    
    # Validate database
    validate_database()
    
    # Close connection
    conn.close()
    print("\nETL process completed successfully. Database: 'class_schedule.db'")

if __name__ == "__main__":
    main()