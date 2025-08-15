import requests
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def convert_timestamp(ts):
    if ts:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return "–"

def load_token_from_txt(filename="token.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read().strip()

def print_trains(data):
    station_name = data.get('station', {}).get('name', 'Неизвестно')
    print("=" * 40)
    print(f"Станція: {station_name}")
    print("=" * 40)

    arrivals = data.get('arrivals', [])
    departures = data.get('departures', [])

    print("\nПрибуття:")
    if arrivals:
        for train in arrivals:
            train_num = train.get('train', '–')
            route = train.get('route', '–')
            time_str = convert_timestamp(train.get('time', 0))
            platform = train.get('platform', '–')
            delay = train.get('delay_minutes')
            delay_str = f" (Затримка: {delay} хв)" if delay else ""
            print(f"  Потяг №{train_num}")
            print(f"    Маршрут: {route}")
            print(f"    Час прибуття: {time_str}")
            print(f"    Платформа: {platform}{delay_str}")
            print("-" * 40)
    else:
        print("  Немає даних про прибуття.")

    print("\nВідправлення:")
    if departures:
        for train in departures:
            train_num = train.get('train', '–')
            route = train.get('route', '–')
            time_str = convert_timestamp(train.get('time', 0))
            platform = train.get('platform', '–')
            print(f"  Потяг №{train_num}")
            print(f"    Маршрут: {route}")
            print(f"    Час відправлення: {time_str}")
            print(f"    Платформа: {platform}")
            print("-" * 40)
    else:
        print("  Немає даних про відправлення.")
token = load_token_from_txt()
if __name__ == "__main__":
    url = "https://app.uz.gov.ua/api/station-boards/2210700"
    headers = {
        "authorization": f"Bearer {token}",
        "accept": "application/json",
        "origin": "https://booking.uz.gov.ua",
        "referer": "https://booking.uz.gov.ua/",
        "x-client-locale": "uk",
        "x-session-id": "4a840b6e-0082-40e0-a401-c1f084d384a9",
        "x-user-agent": "UZ/2 Web/1 User/6090017",
    }

    response = requests.get(url, headers=headers, verify=False)  
    if response.status_code == 200:
        data = response.json()
        print_trains(data)
    else:
        print(f"Помилка {response.status_code}: {response.text}")

