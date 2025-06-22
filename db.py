from sqlalchemy import create_engine, MetaData, Table, select, update, insert, delete, text, Column, Integer, BigInteger, TIMESTAMP, ForeignKey, insert, update, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime
import os
from sqlalchemy.sql import func


DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()
Base = declarative_base()

users = Table('users', metadata, autoload_with=engine)
courses = Table('courses', metadata, autoload_with=engine)
lessons = Table('lessons', metadata, autoload_with=engine)
user_lessons = Table('user_lessons', metadata, autoload_with=engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, nullable=True)
    title = Column(Text, nullable=False)
    video_file_id = Column(Text, nullable=True)
    homework = Column(Text, nullable=True)
    extra_material_file = Column(Text, nullable=True)
    extra_material_link = Column(Text, nullable=True)
    workbook = Column(Text, nullable=True)

class UserLesson(Base):
    __tablename__ = "user_lessons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    status = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    fio = Column(Text, nullable=False)
    username = Column(Text)
    role = Column(Text, nullable=False)
    topic_id = Column(BigInteger)

class RecommendationLetter(Base):
    __tablename__ = "recommendation_letters"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    text = Column(Text)
    photo_id = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

def save_recommendation_letter(user_id: int, text: str | None, photo_id: str | None):
    with SessionLocal() as session:
        letter = RecommendationLetter(
            user_id=user_id,
            text=text,
            photo_id=photo_id
        )
        session.add(letter)
        session.commit()

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

def add_course(title, description, lesson_count, created_by, approved, number_course=None):
    with engine.begin() as conn:
        values = {
            "title": title,
            "description": description,
            "lesson_count": lesson_count,
            "created_by": created_by,
            "approved": approved
        }
        if number_course is not None:
            values["number_course"] = number_course
        result = conn.execute(
            courses.insert().values(**values).returning(courses.c.id)
        )
        course_id = result.scalar()
        return course_id

def add_lesson(course_id, title, video_path, homework, extra_material_file, extra_material_link):
    with engine.begin() as conn:
        conn.execute(
            lessons.insert().values(
                course_id=course_id,
                title=title,
                video_file_id=video_path,
                homework=homework,
                extra_material_file=extra_material_file,
                extra_material_link=extra_material_link
            )
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

def update_lesson_extra_material_file(lesson_id, file_id):
    with engine.begin() as conn:
        conn.execute(
            lessons.update().where(lessons.c.id == lesson_id)
            .values(extra_material_file=file_id)
        )

def update_lesson_extra_material_link(lesson_id, link):
    with engine.begin() as conn:
        conn.execute(
            lessons.update().where(lessons.c.id == lesson_id)
            .values(extra_material_link=link)
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

def get_all_courses():
    with engine.connect() as conn:
        result = conn.execute(
            select(courses.c.id, courses.c.title, courses.c.lesson_count).order_by(courses.c.id)
        )
        return [
            {
                "id": row[0],
                "title": row[1],
                "lesson_count": row[2]
            }
            for row in result.fetchall()
        ]

def get_lessons_by_course(course_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(
                lessons.c.id,
                lessons.c.title,
                lessons.c.video_file_id,
                lessons.c.homework,
                lessons.c.extra_material_file,
                lessons.c.extra_material_link,
                lessons.c.workbook
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
                "extra_material_file": row[4],
                "extra_material_link": row[5],
                "workbook": row[6]
            })
        return lessons_list

def get_course_by_lesson(lesson_id: int):
    with SessionLocal() as session:
        result = session.execute(
            select(lessons.c.course_id).where(lessons.c.id == lesson_id)
        ).scalar()
        if result:
            return session.execute(
                select(courses).where(courses.c.id == result)
            ).mappings().first()
        return None

def get_lesson_by_id(lesson_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(
                lessons.c.id,
                lessons.c.title,
                lessons.c.video_file_id,
                lessons.c.homework,
                lessons.c.extra_material_file,
                lessons.c.extra_material_link,
                lessons.c.workbook
            ).where(lessons.c.id == lesson_id)
        ).fetchone()
        if result:
            return {
                "id": result[0],
                "title": result[1],
                "video_file_id": result[2],
                "homework": result[3],
                "extra_material_file": result[4],
                "extra_material_link": result[5],
                "workbook": result[6],
            }
        return None

def update_user_lesson_status(user_id: int, lesson_id: int, status: str):
    with engine.begin() as conn:
        stmt = user_lessons.update().where(
            (user_lessons.c.user_id == user_id) &
            (user_lessons.c.lesson_id == lesson_id)
        ).values(status=status)
        conn.execute(stmt)
        conn.commit()

def update_course_lesson_count(course_id, count):
    with engine.connect() as conn:
        conn.execute(
            courses.update()
            .where(courses.c.id == course_id)
            .values(lesson_count=count)
        )
        conn.commit()   

def save_homework(user_id, lesson_id, answer=None, file_id=None):
    with engine.begin() as conn:
        stmt = pg_insert(user_lessons).values(
            user_id=user_id,
            lesson_id=lesson_id,
            status='submitted',
            answer=answer,
            file_id=file_id,
            submitted_at=datetime.utcnow()
        ).on_conflict_do_update(
            index_elements=['user_id', 'lesson_id'],
            set_={
                'status': 'submitted',
                'answer': answer,
                'file_id': file_id,
                'submitted_at': datetime.utcnow()
            }
        )
        conn.execute(stmt)

async def notify_admin_about_homework(user_id, lesson_id, text=None, file_id=None):
    # Здесь можно отправить уведомление администратору
    pass

def initialize_user_lessons(user_id: int):
    with engine.connect() as conn:
        # Найти первые уроки всех одобренных курсов
        first_lessons = conn.execute(text("""
            SELECT l.id FROM lessons l
            JOIN courses c ON l.course_id = c.id
            WHERE c.approved = true
            AND l.id IN (
                SELECT MIN(id) FROM lessons GROUP BY course_id
            )
        """)).fetchall()

        for (lesson_id,) in first_lessons:
            # Вставить запись со статусом 'not_started', если нет
            exists = conn.execute(text("""
                SELECT 1 FROM user_lessons WHERE user_id = :user_id AND lesson_id = :lesson_id
            """), {"user_id": user_id, "lesson_id": lesson_id}).fetchone()
            if not exists:
                conn.execute(insert(user_lessons).values(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    status='not_started'
                ))
        conn.commit()

def get_available_courses_for_user(user_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(courses.c.id, courses.c.title)
            .where(courses.c.approved == True)
        ).fetchall()
        return [{"id": r[0], "title": r[1]} for r in result]

def get_first_lesson(course_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(lessons.c.id)
            .where(lessons.c.course_id == course_id)
            .order_by(lessons.c.id)
            .limit(1)
        ).fetchone()
        return result[0] if result else None

def create_or_update_user_lesson(user_id: int, lesson_id: int, status: str):
    with engine.begin() as conn:
        stmt = pg_insert(user_lessons).values(
            user_id=user_id,
            lesson_id=lesson_id,
            status=status
        ).on_conflict_do_update(
            index_elements=['user_id', 'lesson_id'],
            set_={'status': status}
        )
        conn.execute(stmt)

def submit_homework(user_id, lesson_id, answer=None, file_id=None):
    with engine.begin() as conn:
        stmt = pg_insert(user_lessons).values(
            user_id=user_id,
            lesson_id=lesson_id,
            status='submitted',
            answer=answer,
            file_id=file_id,
            submitted_at=datetime.utcnow()
        ).on_conflict_do_update(
            index_elements=['user_id', 'lesson_id'],
            set_={
                'status': 'submitted',
                'answer': answer,
                'file_id': file_id,
                'submitted_at': datetime.utcnow()
            }
        )
        conn.execute(stmt)

def approve_homework(user_id, lesson_id):
    with engine.begin() as conn:
        conn.execute(
            user_lessons.update()
            .where(user_lessons.c.user_id == user_id, user_lessons.c.lesson_id == lesson_id)
            .values(status='approved', checked_at=datetime.utcnow())
        )
        
        # Найти следующий урок
        course_id = conn.execute(
            select(lessons.c.course_id).where(lessons.c.id == lesson_id)
        ).scalar()

        next_lesson = conn.execute(text("""
            SELECT id FROM lessons
            WHERE course_id = :course_id AND id > :lesson_id
            ORDER BY id ASC LIMIT 1
        """), {"course_id": course_id, "lesson_id": lesson_id}).fetchone()

        if next_lesson:
            conn.execute(pg_insert(user_lessons).values(
                user_id=user_id,
                lesson_id=next_lesson[0],
                status='not_started'
            ).on_conflict_do_nothing())

def send_homework_for_redo(user_id, lesson_id, comment):
    with engine.begin() as conn:
        conn.execute(
            user_lessons.update()
            .where(user_lessons.c.user_id == user_id, user_lessons.c.lesson_id == lesson_id)
            .values(status='redo', checked_at=datetime.utcnow(), comment=comment)
        )

def get_lesson_workbook(lesson_id):
    with engine.connect() as conn:
        result = conn.execute(
            select(lessons.c.workbook).where(lessons.c.id == lesson_id)
        ).scalar()
        return result

def get_lesson_extra_materials(lesson_id):
    with engine.connect() as conn:
        result = conn.execute(
            select(
                lessons.c.extra_material_file,
                lessons.c.extra_material_link
            ).where(lessons.c.id == lesson_id)
        ).fetchone()
        if result:
            return {"file_id": result[0], "link": result[1]}
        return None

def check_homework(user_id: int, lesson_id: int, approved: bool, comment: str = None):
    status = 'approved' if approved else 'redo'
    with engine.begin() as conn:
        conn.execute(
            user_lessons.update()
            .where(user_lessons.c.user_id == user_id, user_lessons.c.lesson_id == lesson_id)
            .values(
                status=status,
                comment=comment,
                checked_at=datetime.utcnow()
            )
        )
        # открыть следующий урок
        if approved:
            next_lesson = conn.execute(text("""
                SELECT l2.id FROM lessons l1
                JOIN lessons l2 ON l1.course_id = l2.course_id
                WHERE l1.id = :lesson_id AND l2.id > l1.id
                ORDER BY l2.id
                LIMIT 1
            """), {"lesson_id": lesson_id}).fetchone()
            if next_lesson:
                conn.execute(insert(user_lessons).values(
                    user_id=user_id,
                    lesson_id=next_lesson[0],
                    status='not_started'
                ).on_conflict_do_nothing())

def get_first_course():
    query = select(courses).order_by(courses.c.number_course.asc())
    with engine.connect() as conn:
        return conn.execute(query).mappings().first()

def get_user_lesson_in_progress(user_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(user_lessons.c.lesson_id, user_lessons.c.status)
            .where(user_lessons.c.user_id == user_id)
            .where(user_lessons.c.status.in_(["video_watched", "redo"]))
        ).fetchone()
        if result:
            return {"lesson_id": result[0], "status": result[1]}
        return None

def get_user_by_id(db: Session, user_id: int):
    query = users.select().where(users.c.id == user_id)
    return db.execute(query).first()

def update_homework_status(user_id: int, lesson_id: int, status: str, comment: str = None):
    session = SessionLocal()
    user_lesson = session.query(UserLesson).filter_by(id=user_id, lesson_id=lesson_id).first()
    if user_lesson:
        user_lesson.status = status
        if comment:
            user_lesson.comment = comment
        session.commit()
    session.close()

def get_next_lesson(user_id: int, current_lesson_id: int):
    with engine.connect() as conn:
        course_id = conn.execute(
            select(lessons.c.course_id).where(lessons.c.id == current_lesson_id)
        ).scalar()

        next_lesson = conn.execute(text("""
            SELECT id, title FROM lessons
            WHERE course_id = :course_id AND id > :lesson_id
            ORDER BY id ASC LIMIT 1
        """), {"course_id": course_id, "lesson_id": current_lesson_id}).fetchone()

        if next_lesson:
            return {"id": next_lesson[0], "title": next_lesson[1]}
        return None

def get_next_course_for_user(user_id: int, current_course_id: int):
    print("Текущий курс:", current_course_id)

    with SessionLocal() as session:
        # Получим список всех курсов, отсортированных по ID
        all_courses = session.execute(
            select(courses).order_by(courses.c.number_course)
        ).all()


        # Найдём индекс текущего курса
        current_index = next((i for i, c in enumerate(all_courses) if c.id == current_course_id), None)
        if current_index is None or current_index + 1 >= len(all_courses):
            return None

        next_course = all_courses[current_index + 1]

        # Проверим, есть ли уроки в следующем курсе
        has_lessons = session.execute(
            select(lessons).where(lessons.c.course_id == next_course.id)
        ).first()
        if has_lessons:
            return {
                "id": next_course.id,
                "title": next_course.title
            }
        print("Курсы:", [(c.id, c.number_course) for c in all_courses])
        print("Следующий курс:", next_course.id)
        return None

def save_user_topic_id(user_id: int, topic_id: int):
    with SessionLocal() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.topic_id = topic_id
            session.commit()

def get_user_topic_id(user_id: int) -> int | None:
    with SessionLocal() as session:
        user = session.query(User).filter_by(id=user_id).first()
        return user.topic_id if user else None

def get_user_by_topic_id(topic_id: int):
    with SessionLocal() as session:
        return session.query(User).filter_by(topic_id=topic_id).first()
