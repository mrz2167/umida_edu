from config import ADMIN_GROUP_ID
from db import get_user_topic_id, save_user_topic_id, SessionLocal, get_user_by_id, User

async def ensure_topic(bot, user_id: int, fio: str, username: str) -> int:
    """
    Проверяет, существует ли топик для пользователя.
    Если нет — создаёт и сохраняет в БД.
    Возвращает topic_id.
    """
    topic_id = get_user_topic_id(user_id)
    if topic_id:
        return topic_id

    topic_name = f"{fio} / @{username}" if username else f"{fio} / {user_id}"
    try:
        topic = await bot.create_forum_topic(chat_id=ADMIN_GROUP_ID, name=topic_name)
        topic_id = topic.message_thread_id
        save_user_topic_id(user_id, topic_id)
        return topic_id
    except Exception as e:
        print(f"❗ Ошибка при создании топика для user_id={user_id}: {e}")
        raise


async def generate_topics_for_old_users(bot):
    with SessionLocal() as session:
        users = session.query(User).filter(User.topic_id == None).all()

    for user in users:
        fio = user.fio
        username = user.username or ""
        user_id = user.id

        try:
            topic_id = await ensure_topic(bot, user_id, fio, username)
            save_user_topic_id(user_id, topic_id)
            print(f"✔️ Топик создан: {fio} (@{username}) → {topic_id}")
        except Exception as e:
            print(f"❗ Ошибка при создании топика для user_id={user_id}: {e}")
