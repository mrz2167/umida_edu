import sqlite3

def get_connection():
    conn = sqlite3.connect('database.db')
    return conn

def check_user_role(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_user_role(user_id, fio, username, role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, fio, username, role) VALUES (?, ?, ?, ?)",
                   (user_id, fio, username, role))
    conn.commit()
    conn.close()

def add_course(title, description, lesson_count, user_id, approved):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (title, description, lesson_count, user_id, approved) VALUES (?, ?, ?, ?, ?)",
                   (title, description, lesson_count, user_id, approved))
    conn.commit()
    course_id = cursor.lastrowid
    conn.close()
    return course_id

def add_lesson(course_id, title, video, homework, extra_material):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lessons (course_id, title, video, homework, extra_material) VALUES (?, ?, ?, ?, ?)",
                   (course_id, title, video, homework, extra_material))
    conn.commit()
    conn.close()

def get_all_courses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    conn.close()
    return courses

def get_lessons_by_course(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE course_id = ?", (course_id,))
    lessons = cursor.fetchall()
    conn.close()
    return lessons

def update_course_title(course_id, new_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE courses SET title = ? WHERE id = ?", (new_title, course_id))
    conn.commit()
    conn.close()

def update_course_description(course_id, new_description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE courses SET description = ? WHERE id = ?", (new_description, course_id))
    conn.commit()
    conn.close()

def update_lesson_title(lesson_id, new_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lessons SET title = ? WHERE id = ?", (new_title, lesson_id))
    conn.commit()
    conn.close()

def update_lesson_video(lesson_id, new_video):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lessons SET video = ? WHERE id = ?", (new_video, lesson_id))
    conn.commit()
    conn.close()

def update_lesson_homework(lesson_id, new_homework):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lessons SET homework = ? WHERE id = ?", (new_homework, lesson_id))
    conn.commit()
    conn.close()

def update_lesson_material(lesson_id, new_material):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lessons SET extra_material = ? WHERE id = ?", (new_material, lesson_id))
    conn.commit()
    conn.close()

def delete_course_and_lessons(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lessons WHERE course_id = ?", (course_id,))
    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

def delete_lesson_by_id(lesson_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    conn.commit()
    conn.close()

def get_course_by_id(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    conn.close()
    return course

def approve_course_by_id(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE courses SET approved = ? WHERE id = ?", (True, course_id))
    conn.commit()
    conn.close()