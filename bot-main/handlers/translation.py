"""
Practice flow:
topic -> level -> phrase -> answer -> score
"""

import logging
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message


from db.supabase_client import (
    get_or_create_user,
    save_score
)

from handlers.start import (
    DEFAULT_DIRECTION,
    DEFAULT_LEVEL,
    PracticeState
)

from services.ai_explainer import explain_errors
from services.checker import (
    check_translation,
    format_result_message
)

from services.generator import (
    generate_phrase,
    NoPhraseAvailable
)

from utils.keyboards import (
    after_answer_keyboard,
    direction_label,
    levels_keyboard
)


router = Router()

logger = logging.getLogger(__name__)



# =============================
# TOPIC SELECT
# =============================

@router.callback_query(
    F.data.startswith("topic:")
)
async def topic_chosen(
    callback: CallbackQuery,
    state: FSMContext
):

    topic_id = int(
        callback.data.split(":")[1]
    )


    logger.info(
        f"Topic selected: {topic_id}"
    )


    await state.update_data(
        topic_id=topic_id
    )


    await callback.message.edit_text(
        "📚 <b>Select level:</b>",
        reply_markup=await levels_keyboard(
            topic_id
        ),
        parse_mode="HTML"
    )


    await callback.answer()



# =============================
# LEVEL SELECT
# =============================

@router.callback_query(
    F.data.startswith("level:")
)
async def level_chosen(
    callback: CallbackQuery,
    state: FSMContext
):

    _, topic_id, level = callback.data.split(":")


    topic_id = int(topic_id)


    logger.info(
        f"Level selected: {topic_id=} {level=}"
    )


    await state.update_data(
        topic_id=topic_id,
        level=level
    )


    await callback.message.edit_text(
        "⏳ <b>Loading phrase...</b>",
        parse_mode="HTML"
    )


    await send_phrase(
        callback.message,
        state,
        callback.from_user.id
    )


    await callback.answer()



# =============================
# NEXT PHRASE
# =============================

@router.callback_query(
    F.data.startswith("next:")
)
async def next_phrase(
    callback: CallbackQuery,
    state: FSMContext
):

    _, topic_id, level = callback.data.split(":")


    await state.update_data(
        topic_id=int(topic_id),
        level=level
    )


    await send_phrase(
        callback.message,
        state,
        callback.from_user.id
    )


    await callback.answer()



# =============================
# REPEAT ERRORS
# =============================

@router.callback_query(
    F.data == "repeat_errors"
)
async def repeat_errors(
    callback: CallbackQuery,
    state: FSMContext
):

    result = await send_repeat_phrase(
        callback.message,
        state
    )


    if not result:
        await callback.answer(
            "No mistakes yet",
            show_alert=True
        )
        return


    await callback.answer()



@router.message(Command("repeat"))
@router.message(F.text == "Repeat mistakes")
async def cmd_repeat(
    message: Message,
    state: FSMContext
):

    await send_repeat_phrase(
        message,
        state
    )



# =============================
# SEND PHRASE
# =============================

async def send_phrase(
    message: Message,
    state: FSMContext,
    telegram_id: int
):

    data = await state.get_data()


    topic_id = data.get(
        "topic_id"
    )

    level = data.get(
        "level",
        DEFAULT_LEVEL
    )

    phrase_lang = data.get(
        "phrase_lang",
        DEFAULT_DIRECTION
    )


    if not topic_id:

        await message.answer(
            "Choose topic first"
        )

        return



    await message.answer(
        "⏳ Loading..."
    )



    try:

        user = await get_or_create_user(
            telegram_id,
            None
        )


        phrase = await generate_phrase(
            user_id=user["id"],
            topic_id=topic_id,
            topic_name_ru="",
            topic_name_uz="",
            level=level
        )


    except NoPhraseAvailable:

        await message.answer(
            "No phrases available"
        )

        return


    except Exception as e:

        logger.exception(e)

        await message.answer(
            "Error loading phrase"
        )

        return



    text = (
        phrase["text_uz"]
        if phrase_lang == "uz"
        else phrase["text_ru"]
    )


    await state.update_data(

        current_phrase_id=
        phrase["id"],

        current_text_ru=
        phrase["text_ru"],

        current_text_uz=
        phrase["text_uz"],

        current_english=
        phrase["english_answer"],

        current_alternatives=
        phrase.get(
            "alternative_answers",
            []
        )
    )


    await state.set_state(
        PracticeState.waiting_answer
    )


    await message.answer(

        "📝 <b>Translate:</b>\n"
        "━━━━━━━━━━━━\n"
        f"💬 <b>{escape(text)}</b>\n"
        "━━━━━━━━━━━━\n\n"
        "Send English translation",

        parse_mode="HTML"
    )



# =============================
# ANSWER
# =============================

@router.message(
    PracticeState.waiting_answer
)
async def receive_answer(
    message: Message,
    state: FSMContext
):

    answer = (
        message.text or ""
    ).strip()


    if len(answer) < 2:

        await message.answer(
            "Send translation"
        )

        return



    data = await state.get_data()


    await message.answer(
        "🔍 Checking..."
    )


    result = await check_translation(

        original_ru=
        data.get("current_text_ru",""),

        original_uz=
        data.get("current_text_uz",""),

        reference_english=
        data.get("current_english",""),

        user_answer=
        answer,

        level=
        data.get("level",DEFAULT_LEVEL),

        alternative_answers=
        data.get(
            "current_alternatives",
            []
        ),

        phrase_lang=
        data.get(
            "phrase_lang",
            DEFAULT_DIRECTION
        )
    )



    try:

        user = await get_or_create_user(
            message.from_user.id,
            message.from_user.username
        )


        await save_score(

            user_id=user["id"],

            phrase_id=
            data.get(
                "current_phrase_id"
            ),

            user_answer=answer,

            score=result["score"],

            errors=result["errors"],

            feedback=result["feedback"]
        )


    except Exception as e:

        logger.warning(
            f"Score save error {e}"
        )



    text = format_result_message(

        original_ru=
        data.get("current_text_ru",""),

        original_uz=
        data.get("current_text_uz",""),

        reference=
        data.get("current_english",""),

        user_answer=
        answer,

        result=result,

        lang=
        data.get(
            "phrase_lang",
            DEFAULT_DIRECTION
        ),

        ai_explanation=None
    )


    await message.answer(

        text,

        reply_markup=
        after_answer_keyboard(

            data.get("topic_id"),

            data.get(
                "level",
                DEFAULT_LEVEL
            ),

            result["score"] < 90
        ),

        parse_mode="HTML"
    )



# =============================
# REPEAT
# =============================

async def send_repeat_phrase(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    text = data.get(
        "current_text_ru"
    )


    if not text:
        return False


    await message.answer(
        f"🔁 Try again:\n\n{text}"
    )


    return True
