# src/utils/texts.py

"""
Центральное хранилище для всех текстовых строк, используемых в боте.
Это позволяет легко добавлять новые языки и управлять контентом.
"""

# Тексты для кнопок
BUTTONS = {
    'training': {
        'ru': 'Тренировка',
        'en': 'Training',
        'uz': 'Mashgʻulot',
    },
    'profile': {
        'ru': 'Профиль',
        'en': 'Profile',
        'uz': 'Profil',
    },
    'settings': {
        'ru': 'Настройки',
        'en': 'Settings',
        'uz': 'Sozlamalar',
    },
    'next_phrase': {
        'ru': 'Следующая фраза',
        'en': 'Next phrase',
        'uz': 'Keyingi ibora',
    },
    'change_topic': {
        'ru': 'Сменить тему',
        'en': 'Change topic',
        'uz': 'Mavzuni oʻzgartirish',
    },
    'repeat_errors': {
        'ru': 'Повторение ошибок',
        'en': 'Repeat mistakes',
        'uz': 'Xatolarni takrorlash',
    },
    'notifications_on': {
        'ru': '🔔 Уведомления: Вкл',
        'en': '🔔 Notifications: On',
        'uz': '🔔 Bildirishnomalar: Yoqilgan',
    },
    'notifications_off': {
        'ru': '🔕 Уведомления: Выкл',
        'en': '🔕 Notifications: Off',
        'uz': '🔕 Bildirishnomalar: Oʻchirilgan',
    },
        'edit_profile': {
        'ru': '✏️ Изменить профиль',
        'en': '✏️ Edit Profile',
        'uz': '✏️ Profilni tahrirlash',
    },
    'edit_topic': {
        'ru': '📚 Сменить тему',
        'en': '📚 Change Topic',
        'uz': '📚 Mavzuni oʻzgartirish',
    },
    'edit_level': {
        'ru': '⭐ Сменить уровень',
        'en': '⭐ Change Level',
        'uz': '⭐ Darajani oʻzgartirish',
    },
    'edit_direction': {
        'ru': '🔄 Сменить направление',
        'en': '🔄 Change Direction',
        'uz': '🔄 Yoʻnalishni oʻzgartirish',
    },
    'back_to_profile': {
        'ru': '⬅️ Назад к профилю',
        'en': '⬅️ Back to Profile',
        'uz': '⬅️ Profilga qaytish',
    },
    'back_to_edit_profile': {
        'ru': '⬅️ Назад',
        'en': '⬅️ Back',
        'uz': '⬅️ Orqaga',
    },
    'back_to_edit_profile': {
        'ru': '⬅️ Назад',
        'en': '⬅️ Back',
        'uz': '⬅️ Orqaga',
    },
    # ==================== ДОБАВЬТЕ ЭТИ ТЕКСТЫ ====================
    'edit_language': {
        'ru': '🌐 Сменить язык',
        'en': '🌐 Change Language',
        'uz': '🌐 Tilni oʻzgartirish',
    },
    'back_to_settings': {
        'ru': '⬅️ Назад к настройкам',
        'en': '⬅️ Back to Settings',
        'uz': '⬅️ Sozlamalarga qaytish',
    },
        'repeat_errors_off': {
        'ru': '✅ Повторение ошибок: Вкл',
        'en': '✅ Mistake Repetition: On',
        'uz': '✅ Xatolarni takrorlash: Yoqilgan',
    }
}

# Тексты для сообщений
MESSAGES = {
    'welcome': {
        'ru': 'Добро пожаловать! Выберите опцию в меню.',
        'en': 'Welcome! Please select an option from the menu.',
        'uz': 'Xush kelibsiz! Menudan variant tanlang.',
    },
    'profile_format': {
        'ru': (
            "👤 **Ваш профиль**\n\n"
            "🌐 Язык: {lang}\n"
            "📚 Тема: {topic}\n"
            "⭐ Уровень: {level}\n"
            "📊 Средний балл: {avg_score:.1f}"
        ),
        'en': (
            "👤 **Your Profile**\n\n"
            "🌐 Language: {lang}\n"
            "📚 Topic: {topic}\n"
            "⭐ Level: {level}\n"
            "📊 Average score: {avg_score:.1f}"
        ),
        'uz': (
            "👤 **Sizning profilingiz**\n\n"
            "🌐 Til: {lang}\n"
            "📚 Mavzu: {topic}\n"
            "⭐ Daraja: {level}\n"
            "📊 Oʻrtacha ball: {avg_score:.1f}"
        ),
        
    },
    'topic_finished': {
        'ru': '🎉 Поздравляем! Вы завершили все фразы в этой теме. Вы можете сменить тему в профиле или начать повторение ошибок.',
        'en': '🎉 Congratulations! You have completed all phrases in this topic. You can change the topic in your profile or start repeating mistakes.',
        'uz': '🎉 Tabriklaymiz! Siz bu mavzudagi barcha iboralarni tugatdingiz. Profilingizda mavzuni oʻzgartirishingiz yoki xatolarni takrorlashni boshlashingiz mumkin.',
    },
    'error_occurred': {
        'ru': 'Произошла ошибка. Пожалуйста, попробуйте позже.',
        'en': 'An error occurred. Please try again later.',
        'uz': 'Xatolik yuz berdi. Iltimos, keyinroq qayta urinib koʻring.',
    },
        'choose_topic': {
        'ru': 'Пожалуйста, выберите новую тему:',
        'en': 'Please select a new topic:',
        'uz': 'Iltimos, yangi mavzuni tanlang:',
    },
    'choose_level': {
        'ru': 'Пожалуйста, выберите новый уровень:',
        'en': 'Please select a new level:',
        'uz': 'Iltimos, yangi darajani tanlang:',
    },
    'choose_direction': {
        'ru': 'Пожалуйста, выберите направление перевода:',
        'en': 'Please select the translation direction:',
        'uz': 'Iltimos, tarjima yoʻnalishini tanlang:',
    },
    'profile_updated': {
        'ru': '✅ Профиль обновлен!',
        'en': '✅ Profile updated!',
        'uz': '✅ Profil yangilandi!',
    },
    # ==================== ДОБАВЬТЕ ЭТИ ТЕКСТЫ ====================
    'choose_language': {
        'ru': 'Пожалуйста, выберите язык интерфейса:',
        'en': 'Please select the interface language:',
        'uz': 'Iltimos, interfeys tilini tanlang:',
    },
    'language_updated': {
        'ru': '✅ Язык обновлен!',
        'en': '✅ Language updated!',
        'uz': '✅ Til yangilandi!',
    },
    'notifications_on_msg': {
        'ru': '✅ Уведомления включены.',
        'en': '✅ Notifications enabled.',
        'uz': '✅ Bildirishnomalar yoqildi.',
    },
    'notifications_off_msg': {
        'ru': '🔕 Уведомления выключены.',
        'en': '🔕 Notifications disabled.',
        'uz': '🔕 Bildirishnomalar oʻchirildi.',
    },
    'repeat_errors_on': {
        'ru': '✅ Режим повторения ошибок включен. Нажмите "Тренировка", чтобы начать.',
        'en': '✅ Mistake repetition mode is ON. Press "Training" to start.',
        'uz': '✅ Xatolarni takrorlash rejimi yoqildi. Boshlash uchun "Mashgʻulot" tugmasini bosing.',
    },
    'no_errors_to_repeat': {
        'ru': '🎉 У вас нет ошибок для повторения в этой теме! Так держать!',
        'en': '🎉 You have no mistakes to repeat in this topic! Keep it up!',
        'uz': '🎉 Bu mavzuda takrorlash uchun xatolaringiz yoʻq! Barakalla!',
    },
        'repeat_errors_off_msg': {
        'ru': 'Режим повторения ошибок выключен.',
        'en': 'Mistake repetition mode is OFF.',
        'uz': 'Xatolarni takrorlash rejimi oʻchirildi.',
    }
}

# Гипотетическая функция для удобного получения текста (можно не использовать и обращаться напрямую)
def get_text(key: str, lang: str, category: str = 'MESSAGES') -> str:
    """
    Возвращает текст по ключу и языку.
    """
    data = globals().get(category.upper())
    if not data or key not in data or lang not in data[key]:
        return "..."  # Возвращаем заглушку, если текст не найден
    return data[key][lang]