import datetime
import json
import logging
import os
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_instance = redis.from_url(os.environ['REDIS_URL'])

TOTAL_DB_FILES = 5
DB_FILE_STR = 'files/recareas-{file_id}-of-{total_files}.json'

def format_weather_dict_dates(weather_dict):
    '''
    Convert dates from day numbers to datetime.dates for a the current year.
    '''
    formatted_weather_dict = {}
    for day_num_str, weather_dict in weather_dict.iteritems():
        day_num = int(day_num_str)
        this_year = datetime.date.today().year
        this_date = (
            datetime.date(this_year, 1, 1) + datetime.timedelta(day_num - 1)
        )

        this_date_str = this_date.strftime('%Y-%m-%d')
        formatted_weather_dict[this_date_str] = weather_dict

    return formatted_weather_dict

def initialize_redis_content():
    '''
    Initialize redis database with contents of the weather-enriched recarea
    file.
    '''
    db_str_list = []
    for i in range(1, TOTAL_DB_FILES + 1):
        this_db_chunk_filename = DB_FILE_STR.format(file_id=i,
                                                    total_files=TOTAL_DB_FILES)

        with open(this_db_chunk_filename) as filehandle:
            db_str_list.append(filehandle.read())

    entire_db_str = ''.join(db_str_list)
    recarea_dict = json.loads(entire_db_str)

    for recarea_id_str, recarea in recarea_dict.iteritems():
        if recarea.get('RecAreaWeatherDict'):
            recarea['RecAreaWeatherDict'] = format_weather_dict_dates(
                recarea['RecAreaWeatherDict']
            )

        small_recarea_dict = {'RecAreaID': recarea['RecAreaID'],
                              'RecAreaLatitude': recarea['RecAreaLatitude'],
                              'RecAreaLongitude': recarea['RecAreaLongitude'],
                              'RecAreaName': recarea['RecAreaName']}

        redis_instance.set(recarea_id_str, json.dumps(recarea))
        redis_instance.set(recarea_id_str + '_small',
                           json.dumps(small_recarea_dict))

if __name__ == '__main__':
    initialize_redis_content()
