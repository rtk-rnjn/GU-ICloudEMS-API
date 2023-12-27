BEGIN;

CREATE TABLE IF NOT EXISTS students_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_number TEXT NOT NULL,
    password TEXT NOT NULL,
    section INTEGER NOT NULL,

    UNIQUE(admission_number)
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    admission_number TEXT NOT NULL,
    application_number TEXT NOT NULL,
    father_name TEXT NOT NULL,
    fee_category TEXT,
    dob TEXT,
    gender TEXT,
    nationality TEXT,
    religion TEXT,
    local_address TEXT,
    permanent_address TEXT,
    city TEXT,
    state TEXT,
    zip_code INTEGER,
    emergency_contact INTEGER,
    email TEXT,
    user_id TEXT NOT NULL,
    class TEXT NOT NULL,
    semester TEXT NOT NULL,
    roll_no INTEGER NOT NULL,
    eligibility_number TEXT NOT NULL,
    prn_number INTEGER NOT NULL,

    UNIQUE(admission_number),
    UNIQUE(roll_no)
);

CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT,
    end_time TEXT,
    faculty_name TEXT NOT NULL,
    slot_id INTEGER NOT NULL,
    class TEXT NOT NULL,

    UNIQUE(start_time, end_time, faculty_name, slot_id, class)
);

CREATE TABLE IF NOT EXISTS alternative_timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT,
    end_time TEXT,
    faculty_name TEXT NOT NULL,
    alternative_faculty_name TEXT NOT NULL,
    slot_id INTEGER NOT NULL,
    class TEXT NOT NULL,

    UNIQUE(start_time, end_time, faculty_name, alternative_faculty_name, slot_id, class)
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    course_name TEXT NOT NULL,

    UNIQUE(course_code)
);

CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT,
    course_name TEXT,
    course_type TEXT,
    section INTEGER,
    room TEXT,
    block TEXT,
    UNIQUE(course_code, section, course_type, section, room, block)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_number TEXT NOT NULL,
    class TEXT NOT NULL,
    section INTEGER NOT NULL,
    course_code TEXT NOT NULL,
    total_classes INTEGER NOT NULL,
    attended_classes INTEGER NOT NULL,

    UNIQUE(admission_number, class, section, course_code)
);

COMMIT;
