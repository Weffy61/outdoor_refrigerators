import os
import textwrap
from os.path import join, normpath
from urllib.parse import urlparse, unquote

import PIL.Image
import pillow_heif
import requests
from django.conf import settings
from exif import Image


def get_file_naming(file_path):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    file_extension = os.path.splitext(file_path)[-1].lower()
    return file_name, file_extension


def convert_extension(heic_file_path):
    heif_file = pillow_heif.read_heif(heic_file_path)
    image = PIL.Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        'raw',
        heif_file.mode,
        heif_file.stride
    )
    image_info = heif_file.info
    image_exif = image_info['exif']
    base, _ = os.path.splitext(heic_file_path)
    file_path = f"{base}.jpg"
    image.save(file_path, 'JPEG', exif=image_exif)
    return file_path


def get_file_path(img_path):
    relative_path = urlparse(img_path).path
    decoded_path = unquote(relative_path)
    file_path = normpath(join(settings.BASE_DIR, decoded_path.lstrip('/')))
    return file_path, relative_path


def check_exif(img_path):
    file_path, relative_path = get_file_path(img_path)
    file_name, file_extension = get_file_naming(file_path)
    if file_extension == '.heic':
        file_path = convert_extension(file_path)

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
{device_brand.lstrip()},
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


def extract_gps_coords(img_path):
    try:
        file_path, _ = get_file_path(img_path)
        _, file_extension = get_file_naming(file_path)
        if file_extension == '.heic':
            file_path = convert_extension(file_path)
        with open(file_path, 'rb') as img_file:
            img = Image(img_file)
        exif_params = img.get_all()
        lat = round(convert_coords(*(exif_params['gps_latitude'])), 6) \
            if exif_params.get('gps_latitude') else None
        lng = round(convert_coords(*(exif_params['gps_longitude'])), 6) \
            if exif_params.get('gps_longitude') else None
        return lat, lng
    except Exception:
        return None, None


def convert_coords(degrees, minutes, seconds):
    decimal_degrees = degrees + (minutes / 60.0) + (seconds / 3600.0)
    return decimal_degrees


def get_place(latitude, longitude):
    from django.conf import settings
    api_key = getattr(settings, 'YANDEX_GEOCODER_API_KEY', None)
    if not api_key:
        return 'Яндекс API-ключ не настроен'
    try:
        payload = {
            'geocode': f'{longitude},{latitude}',
            'apikey': api_key,
            'format': 'json',
            'lang': 'ru_RU',
            'results': 1,
        }
        response = requests.get(
            'https://geocode-maps.yandex.ru/1.x/',
            params=payload,
            timeout=3,
        )
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.HTTPError, requests.exceptions.MissingSchema,
            requests.exceptions.ConnectionError, requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout) as ex:
        return f'Проблема с получением данных местоположения - проблема с сервисом. Ошибка: {ex}'


def parse_location(place_response):
    if isinstance(place_response, str):
        return place_response

    try:
        members = (
            place_response['response']['GeoObjectCollection']['featureMember']
        )
        if not members:
            return 'Местоположение не определено\n'

        components = (
            members[0]['GeoObject']
            ['metaDataProperty']['GeocoderMetaData']
            ['Address']['Components']
        )
        kind_map = {c['kind']: c['name'] for c in components}

        country = kind_map.get('country', 'Страна отсутствует')
        region = kind_map.get('province', 'Регион отсутствует')
        city = kind_map.get('locality', 'Город отсутствует')
        area = kind_map.get('district', 'Район отсутствует')
        street = kind_map.get('street', '')
        house = kind_map.get('house', '')

        address_line = f'{street}, {house}'.strip(', ') if street else ''

        place_content = textwrap.dedent(f'''
    Страна: {country}
    Регион: {region}
    Город: {city}
    Район: {area}
    {f"Адрес: {address_line}" if address_line else ""}
    ''')
        return place_content
    except (KeyError, IndexError, TypeError):
        return 'Не удалось разобрать ответ геокодера\n'
