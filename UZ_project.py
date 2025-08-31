import requests
import urllib3
from datetime import datetime
from config import headers, STATIONS, TELEGRAM_TOKEN
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import logging

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конвертация timestamp в время
def convert_timestamp_to_time(ts):
    if ts:
        return datetime.fromtimestamp(ts).strftime("%H:%M")
    return "–"

# Формирование таблицы
def format_table(title, trains, col_widths):
    headers_dict = {"num": "Потяг", "route": "Сполучення", "time": "Час", "platform": "Колія"}
    separator = "├"
    for key in ["num", "route", "time", "platform"]:
        separator += "─" * (col_widths[key] + 2) + "┼"
    separator = separator[:-1] + "┤"
    top_border = "┌" + separator[1:-1].replace("┼", "┬") + "┐"
    bottom_border = "└" + separator[1:-1].replace("┼", "┴") + "┘"

    table = top_border + "\n"
    table += f"│ {title.center(len(separator) - 4)} │\n"
    table += separator + "\n"
    header_line = "│"
    for key, header in headers_dict.items():
        header_line += f" {header.center(col_widths[key])} │"
    table += header_line + "\n" + separator + "\n"

    if not trains:
        table += f"│ {'Немає даних'.center(len(separator) - 4)} │\n"
    else:
        for train in trains:
            train_num = str(train.get("train", "–"))
            route = train.get("route", "–")
            time_str = convert_timestamp_to_time(train.get("time", 0))
            platform = str(train.get("platform", "–"))
            data_line = (f"│ {train_num.ljust(col_widths['num'])} "
                         f"│ {route.ljust(col_widths['route'])} "
                         f"│ {time_str.center(col_widths['time'])} "
                         f"│ {platform.center(col_widths['platform'])} │")
            table += data_line + "\n"

    table += bottom_border
    return table

# Главное меню с выбором станции
def station_keyboard():
    return ReplyKeyboardMarkup([[city.capitalize()] for city in STATIONS.keys()],
                               resize_keyboard=True)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Виберіть станцію:", reply_markup=station_keyboard())
    logger.info(f"Пользователь {update.effective_user.first_name} начал работу с ботом")

# Получение расписания
async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_input = update.message.text.strip()
    station_id = STATIONS.get(city_input.lower())

    if not station_id:
        available_cities = ", ".join([c.capitalize() for c in STATIONS.keys()])
        await update.message.reply_text(f"Станцію '{city_input}' не знайдено.\nСпробуйте: {available_cities}",
                                        reply_markup=station_keyboard())
        return

    url = f"https://app.uz.gov.ua/api/station-boards/{station_id}"
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()

        station_name = data.get("station", {}).get("name", "Невідомо")
        arrivals = data.get("arrivals", [])
        departures = data.get("departures", [])

        if not arrivals and not departures:
            await update.message.reply_text(f"Для станції '{station_name}' немає даних електронного табло.",
                                            reply_markup=station_keyboard())
            return

        col_widths = {"num": 6, "route": 35, "time": 7, "platform": 7}
        text = f"=== Розклад по станції: {station_name} ===\n\n"
        text += format_table("→ Відправлення", departures, col_widths) + "\n\n"
        text += format_table("→ Прибуття", arrivals, col_widths)

        await update.message.reply_text(f"<pre>{text}</pre>", parse_mode="HTML", reply_markup=station_keyboard())

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к API: {e}")
        await update.message.reply_text(f"Помилка запиту до API: {e}", reply_markup=station_keyboard())
    except Exception as e:
        logger.exception("Произошла ошибка")
        await update.message.reply_text("Сталася непередбачена помилка. Спробуйте ще раз.",
                                        reply_markup=station_keyboard())

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_schedule))
    logger.info("Бот запускается...")
    app.run_polling()
    logger.info("Бот запущен!")


