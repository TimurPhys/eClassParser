from telegram.ext import Application
from handlers.conv_chain import setup_handlers, start_commands
from data_parse.parse import init_db

TOKEN = "8011583878:AAFAeLhqtM2meK8GM88y_lYLX97Pmx8kJgQ"

async def setup(application: Application):
    await application.bot.set_my_commands(start_commands)
    # asyncio.create_task(check_inactivity(application))
    # asyncio.create_task(selenium_frequent_request(application))


def main() -> None:
    # Создаем Application вместо Updater
    application = Application.builder().token(TOKEN).post_init(setup).build()

    setup_handlers(application)

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    init_db()
    main()