from sqlalchemy import create_engine, MetaData, Table, select, update, insert, delete, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()

users = Table('users', metadata, autoload_with=engine)
courses = Table('courses', metadata, autoload_with=engine)
lessons = Table('lessons', metadata, autoload_with=engine)

def check_user_role(user_id):
    with engine.connect() as conn:
        query = select(users.c.role).where(users.c.id == user_id)
        result = conn.execute(query).fetchone()
        return result[0] if result else None

def add_user_role(user_id: int, fio: str, username: str, role: str):
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    with engine.begin() as conn:
        ins = pg_insert(users).values(id=user_id, fio=fio, username=username, role=role)
        ins = ins.on_conflict_do_update(
            index_elements=[users.c.id],
            set_={"role": role, "fio": fio, "username": username}
        )
        conn.execute(ins)

def add_course(title, description, lesson_count, created_by, approved):
    with engine.begin() as conn:
        result = conn.execute(
            courses.insert().values(
                title=title,
                description=description,
                lesson_count=lesson_count,
                created_by=created_by,
                approved=approved
            ).returning(courses.c.id)
        )
        course_id = result.scalar()
        return course_id

def add_lesson(course_id, title, video_path, homework, extra_materials):
    with engine.begin() as conn:
        conn.execute(
            lessons.insert().values(
                course_id=course_id,
                title=title,
                video_file_id=video_path,
                homework=homework,
                extra_materials=extra_materials
            )
        )
        conn.execute(
            courses.update().where(courses.c.id == course_id)
            .values(lesson_count=courses.c.lesson_count + 1)
        )

def approve_course_by_id(course_id: int):
    with engine.begin() as conn:
        conn.execute(
            courses.update().where(courses.c.id == course_id)
            .values(approved=True)
        )

def delete_course_and_lessons(course_id: int):
    with engine.begin() as conn:
        conn.execute(
            lessons.delete().where(lessons.c.course_id == course_id)
        )
        conn.execute(
            courses.delete().where(courses.c.id == course_id)
        )

def delete_lesson_by_id(lesson_id):
    with engine.begin() as conn:
        # Получаем course_id для уменьшения lesson_count
        result = conn.execute(
            select(lessons.c.course_id).where(lessons.c.id == lesson_id)
        ).fetchone()
        course_id = result[0] if result else None
        conn.execute(
            lessons.delete().where(lessons.c.id == lesson_id)
        )
        if course_id:
            conn.execute(
                courses.update().where(courses.c.id == course_id)
                .values(lesson_count=courses.c.lesson_count - 1)
            )

def update_course_title(course_id: int, new_title: str):
    with engine.begin() as conn:
        conn.execute(
            courses.update().where(courses.c.id == course_id)
            .values(title=new_title)
        )

def update_course_description(course_id: int, new_description: str):
    with engine.begin() as conn:
        conn.execute(
            courses.update().where(courses.c.id == course_id)
            .values(description=new_description)
        )

def update_lesson_title(lesson_id: int, new_title: str):
    with engine.begin() as conn:
        conn.execute(
            lessons.update().where(lessons.c.id == lesson_id)
            .values(title=new_title)
        )

def update_lesson_video(lesson_id: int, new_video_file_id: str):
    with engine.begin() as conn:
        conn.execute(
            lessons.update().where(lessons.c.id == lesson_id)
            .values(video_file_id=new_video_file_id)
        )

def update_lesson_homework(lesson_id: int, new_homework: str):
    with engine.begin() as conn:
        conn.execute(
            lessons.update().where(lessons.c.id == lesson_id)
            .values(homework=new_homework)
        )

def update_lesson_material(lesson_id: int, new_material_file_id):
    with engine.begin() as conn:
        conn.execute(
            lessons.update().where(lessons.c.id == lesson_id)
            .values(extra_materials=new_material_file_id)
        )

def get_course_by_id(course_id):
    with engine.connect() as conn:
        result = conn.execute(
            select(courses.c.id, courses.c.title, courses.c.description)
            .where(courses.c.id == course_id)
        ).fetchone()
        if result:
            return {"id": result[0], "title": result[1], "description": result[2]}
        return None

def get_lessons_by_course(course_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(
                lessons.c.id,
                lessons.c.title,
                lessons.c.video_file_id,
                lessons.c.homework,
                lessons.c.extra_materials
            ).where(lessons.c.course_id == course_id)
            .order_by(lessons.c.id)
        )
        lessons_list = []
        for row in result.fetchall():
            lessons_list.append({
                "id": row[0],
                "title": row[1],
                "video_file_id": row[2],
                "homework": row[3],
                "extra_materials": row[4],
            })
        return lessons_list

def get_all_courses():
    with engine.connect() as conn:
        result = conn.execute(
            select(courses.c.id, courses.c.title).order_by(courses.c.id)
        )
        return [{"id": row[0], "title": row[1]} for row in result.fetchall()]