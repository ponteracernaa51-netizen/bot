import os
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application
)

from config import BOT_TOKEN

from handlers import start, stats, translation
from utils.antispam import AntiSpamMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


WEBHOOK_PATH = "/webhook"



def create_app():

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )


    dp = Dispatcher(
        storage=MemoryStorage()
    )


    # -------------------------
    # Middleware
    # -------------------------

    dp.message.middleware(
        AntiSpamMiddleware()
    )

    dp.callback_query.middleware(
        AntiSpamMiddleware()
    )



    # -------------------------
    # Routers
    # -------------------------

    dp.include_router(start.router)
    dp.include_router(stats.router)
    dp.include_router(translation.router)



    # -------------------------
    # Startup
    # -------------------------

    async def on_startup(bot: Bot):

        logging.info(
            "🚀 BOT STARTING"
        )

        import asyncio
        async def bg_preload():
            try:
                from services.checker import preload_models
                await asyncio.to_thread(preload_models)
            except Exception as e:
                logging.warning(
                    f"Failed to preload models in background: {e}"
                )

        asyncio.create_task(bg_preload())


        render_url = os.getenv(
            "RENDER_EXTERNAL_URL"
        )


        logging.info(
            f"Render URL: {render_url}"
        )


        if not render_url:
            raise Exception(
                "RENDER_EXTERNAL_URL missing"
            )


        if not render_url.startswith("http"):
            render_url = (
                "https://" + render_url
            )


        webhook_url = (
            f"{render_url}{WEBHOOK_PATH}"
        )


        await bot.set_webhook(
            webhook_url,
            drop_pending_updates=True,
            allowed_updates=[
                "message",
                "callback_query"
            ]
        )


        info = await bot.get_webhook_info()


        logging.info(
            f"✅ WEBHOOK ACTIVE: {info.url}"
        )



    # -------------------------
    # Shutdown
    # -------------------------

    async def on_shutdown(bot: Bot):

        logging.info(
            "🛑 BOT STOPPING"
        )


        await bot.session.close()


        logging.info(
            "Bot shutdown completed"
        )



    dp.startup.register(
        on_startup
    )

    dp.shutdown.register(
        on_shutdown
    )



    # -------------------------
    # APP
    # -------------------------

    app = web.Application()



    # health check Render

    async def health(request):

        return web.Response(
            text="Bot is alive"
        )


    app.router.add_get(
        "/",
        health
    )



    # webhook handler

    SimpleRequestHandler(
        dp,
        bot
    ).register(
        app,
        path=WEBHOOK_PATH
    )



    # aiogram lifecycle

    setup_application(
        app,
        dp,
        bot=bot
    )


    return app




try:
    app = create_app()
    logging.info("✅ APP CREATED SUCCESSFULLY")

except Exception as e:
    logging.exception(
        f"❌ APP CREATION FAILED: {e}"
    )
    raise



if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            10000
        )
    )


    logging.info(
        f"🌐 STARTING SERVER ON PORT {port}"
    )


    web.run_app(
        app,
        host="0.0.0.0",
        port=port
    )
