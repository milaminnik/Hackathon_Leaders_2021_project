import re
import thefuzz
from thefuzz import process
import pandas as pd


def coordinates_preprocessor(coordinates):
    '''
        Убирает запятые.
        Плюс добавим сюда любую другую предобработку таблицы координат.
    '''
    try:
        coordinates['text'] = coordinates['text'].apply(lambda x: re.sub(',', '', x))
        return coordinates
    except:
        return coordinates


def get_full_name_coordinates(full_name_list, coordinates):
    '''
        Возвращает координаты только найденных ФИО.
    '''
    if isinstance(coordinates, pd.DataFrame): #добавил это условие, потом что иногда пустые координаты могут приходить, если нет текста на странице
        сoordinates_clear = coordinates_preprocessor(coordinates)
        full_name_in_table = сoordinates_clear.query(f'text in {full_name_list}')['text'].tolist()
        texts = сoordinates_clear.query(f'text not in {full_name_list}')['text']
        name_not_in_table = [name for name in full_name_list if name not in full_name_in_table]
        if len(name_not_in_table) > 0:
            for name in name_not_in_table:
                word = process.extractOne(name, texts)[0]
                full_name_list.remove(name)
                full_name_list.append(word)
        ner_coordinates = сoordinates_clear.query(f'text in {full_name_list}')
        return ner_coordinates.reset_index(drop=True)
