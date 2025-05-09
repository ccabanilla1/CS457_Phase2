-- SQL Validation Script for Class Schedule Database
-- This script confirms the accuracy and sufficiency of the database

-- Enable column headers and formatted output
.headers on
.mode column
.width 30 30 30 30

-- 1. Basic Database Structure Validation
-- List all tables in the database
.print "\n=== Database Tables ==="
.tables

-- Show schema for each table
.print "\n=== Department Table Schema ==="
.schema department

.print "\n=== Course Table Schema ==="
.schema course

.print "\n=== Term Table Schema ==="
.schema term

.print "\n=== Instructor Table Schema ==="
.schema instructor

.print "\n=== Section Table Schema ==="
.schema section

.print "\n=== Building Table Schema ==="
.schema building

.print "\n=== Schedule Table Schema ==="
.schema schedule

-- 2. Data Validation - Count records in each table
.print "\n=== Record Counts ==="
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

-- 3. Sample Data Validation - Sample records from each table
.print "\n=== Sample Department Data ==="
SELECT * FROM department LIMIT 5;

.print "\n=== Sample Course Data ==="
SELECT * FROM course LIMIT 5;

.print "\n=== Sample Term Data ==="
SELECT * FROM term LIMIT 5;

.print "\n=== Sample Instructor Data ==="
SELECT * FROM instructor LIMIT 5;

.print "\n=== Sample Section Data ==="
SELECT * FROM section LIMIT 5;

.print "\n=== Sample Building Data ==="
SELECT * FROM building LIMIT 5;

.print "\n=== Sample Schedule Data ==="
SELECT * FROM schedule LIMIT 5;

-- 4. Relationship Validation - Check foreign key relationships

.print "\n=== Courses per Department ==="
SELECT d.dept_name, COUNT(c.course_id) as Course_Count
FROM department d
LEFT JOIN course c ON d.dept_id = c.dept_id
GROUP BY d.dept_name
ORDER BY Course_Count DESC;

.print "\n=== Sections per Course (Top 10) ==="
SELECT c.course_name, COUNT(s.section_id) as Section_Count
FROM course c
LEFT JOIN section s ON c.course_id = s.course_id
GROUP BY c.course_name
ORDER BY Section_Count DESC
LIMIT 10;

.print "\n=== Teaching Load per Instructor (Top 10) ==="
SELECT i.last_name, i.first_name, COUNT(s.section_id) as Section_Count
FROM instructor i
LEFT JOIN section s ON i.instr_id = s.instr_id
GROUP BY i.last_name, i.first_name
ORDER BY Section_Count DESC
LIMIT 10;

.print "\n=== Building Usage (Schedules per Building) ==="
SELECT b.bldg_name, COUNT(sch.schedule_id) as Schedule_Count
FROM building b
LEFT JOIN schedule sch ON b.bldg_id = sch.bldg_id
GROUP BY b.bldg_name
ORDER BY Schedule_Count DESC;

-- 5. Complex Queries - Testing database functionality

.print "\n=== Complete Class Schedule (Sample) ==="
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
ORDER BY d.dept_name, c.course_num, s.section_num
LIMIT 10;

.print "\n=== Sections with Highest Enrollment Capacity ==="
SELECT 
    c.course_num,
    c.course_name,
    s.section_num,
    i.last_name,
    i.first_name,
    s.max_seats
FROM section s
JOIN course c ON s.course_id = c.course_id
JOIN instructor i ON s.instr_id = i.instr_id
ORDER BY s.max_seats DESC
LIMIT 10;

.print "\n=== Class Days Distribution ==="
SELECT 
    SUBSTR(sch.day_pattern, 1, 2) as Day,
    COUNT(sch.schedule_id) as Class_Count
FROM schedule sch
WHERE SUBSTR(sch.day_pattern, 1, 1) IN ('M', 'T', 'W', 'R', 'F')
GROUP BY Day
ORDER BY 
    CASE Day
        WHEN 'M' THEN 1
        WHEN 'T' THEN 2
        WHEN 'W' THEN 3
        WHEN 'R' THEN 4
        WHEN 'F' THEN 5
        ELSE 6
    END;

.print "\n=== Room Utilization (Top 10) ==="
SELECT 
    b.bldg_name,
    sch.room_num,
    COUNT(sch.schedule_id) as Usage_Count
FROM schedule sch
JOIN building b ON sch.bldg_id = b.bldg_id
GROUP BY b.bldg_id, sch.room_num
ORDER BY Usage_Count DESC
LIMIT 10;

.print "\n=== Potential Scheduling Conflicts (Same Room, Same Time) ==="
SELECT 
    a.section_id as Section_A,
    b.section_id as Section_B,
    c1.course_num as Course_A,
    c2.course_num as Course_B,
    bldg.bldg_name,
    a.room_num,
    a.day_pattern
FROM schedule a
JOIN schedule b ON a.bldg_id = b.bldg_id AND a.room_num = b.room_num AND a.day_pattern = b.day_pattern
JOIN section s1 ON a.section_id = s1.section_id
JOIN section s2 ON b.section_id = s2.section_id
JOIN course c1 ON s1.course_id = c1.course_id
JOIN course c2 ON s2.course_id = c2.course_id
JOIN building bldg ON a.bldg_id = bldg.bldg_id
WHERE a.section_id < b.section_id
ORDER BY bldg.bldg_name, a.room_num, a.day_pattern
LIMIT 10;

.print "\n=== Course Offerings by Department ==="
SELECT 
    d.dept_name,
    COUNT(DISTINCT c.course_id) as Course_Count,
    COUNT(s.section_id) as Section_Count
FROM department d
JOIN course c ON d.dept_id = c.dept_id
JOIN section s ON c.course_id = s.course_id
GROUP BY d.dept_id
ORDER BY Section_Count DESC;

.print "\n=== Database Validation Complete ==="