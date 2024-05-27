import textwrap
from os.path import join, normpath
from urllib.parse import urlparse, unquote

import requests
from django.conf import settings
from exif import Image


def check_exif(img_path):
    relative_path = urlparse(img_path).path
    decoded_path = unquote(relative_path)
    file_path = normpath(join(settings.BASE_DIR, decoded_path.lstrip('/')))

    with open(file_path, 'rb') as img_file:
        img = Image(img_file)
    exif_params = img.get_all()

    file = f'Путь анализируемого файла: {relative_path}'
    device_brand = f"Марка устройства: " \
                   f"{exif_params.get('make', 'Марка устройства отсутствует')}"
    device_model = f"Модель устройства: " \
                   f"{exif_params.get('model', 'Модель устройства отсутствует')}"
    os_version = f"Версиия операционной системы: " \
                 f"{exif_params.get('software', 'Версиия операционной системы отсутствует')}"
    lens_brand = f"Марка линзы устройства: " \
                 f"{exif_params.get('lens_make', 'Марка линзы устройства отсутствует')}"
    lens_model = f"Модель линзы устройства: " \
                 f"{exif_params.get('lens_model', 'Модель линзы устройства отсутствует')}"

    gps_longitude_converted = round(convert_coords(*(exif_params.get('gps_longitude'))), 4) \
        if exif_params.get('gps_longitude') else None
    gps_latitude_converted = round(convert_coords(*(exif_params.get('gps_latitude'))), 4) \
        if exif_params.get('gps_latitude') else None
    gps_longitude = f"Долгота: {gps_longitude_converted if gps_longitude_converted else 'Долгота отсутствует'}"
    gps_latitude = f"Широта: {gps_latitude_converted if gps_latitude_converted else 'Широта отсутствует'}"

    place = get_place(gps_latitude_converted, gps_longitude_converted) \
        if gps_latitude_converted and gps_latitude_converted \
        else 'Невозможно установить местоположение, отсутствуют координаты'
    place_details = 'Данные местоположения: Невозможно получить по причине отсутствия координат'
    if place != 'Невозможно установить местоположение, отсутствуют координаты':
        place_details = parse_location(place)
        gps_datestamp = f"Дата сьемки по GPS: " \
                        f"{exif_params.get('gps_datestamp', 'Отсутствует, фото вероятно изменялось')}"

        speed_unit = 'Еденица измерения скорости: км' if exif_params.get('gps_speed_ref') == 'K' else \
            'Еденица измерения скорости: неверная, либо отсутствует'
        place_details += f'{gps_datestamp},\n{speed_unit}\n'
    datetime_created_bad = 'Дата отсутствует - фото изменялось(отсутствует показатель сьемки камерой)'
    datetime_created = f"Фото сделано: " \
                       f"{exif_params.get('datetime_original', datetime_created_bad)}"
    datetime_changed = exif_params.get('datetime')
    datetime_digital = exif_params.get('datetime_digitized')

    date_problems = 'Подозрение на изменение фото в области времени: Отсутствует' \
        if exif_params.get('datetime_original') == datetime_changed == datetime_digital else \
        'Подозрение на изменение фото в области времени: Фото изменялось '
    report_test = textwrap.dedent(f'''
    Анализируемый файл:
    {file}

    Информация по устройству:
    {device_brand},
    {device_model},
    {os_version},
    {lens_brand},
    {lens_model}

    Информация по анализу GPS:
    {gps_latitude},
    {gps_longitude},
    {place_details}

    Информациия по анализу времени:
    {datetime_created},
    {date_problems}
    ''')
    return report_test


def convert_coords(degrees, minutes, seconds):
    decimal_degrees = degrees + (minutes / 60.0) + (seconds / 3600.0)
    return decimal_degrees


def get_place(latitude, longitude):
    try:
        payload = {
            'latitude': latitude,
            'longitude': longitude,
            'localityLanguage': 'ru'

        }
        response = requests.get('https://api.bigdatacloud.net/data/reverse-geocode-client', params=payload, timeout=3)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.HTTPError, requests.exceptions.MissingSchema,
            requests.exceptions.ConnectionError, requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout) as ex:
        return f'Проблема с получением данных местоположения - проблема с сервисом. Ошибка: {ex}'


def parse_location(place_response):
    country = place_response.get('countryName', 'Страна отсутствует')
    region = place_response.get('principalSubdivision', 'Регион отсутствует')
    city = place_response.get('city', 'Город отсутствует')
    area = place_response.get('locality', 'Район отсутствует')
    place_content = textwrap.dedent(f'''
    Страна: {country}
    Регион: {region}
    Город: {city}
    Район: {area}
    ''')
    return place_content
