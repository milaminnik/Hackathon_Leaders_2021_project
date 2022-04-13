from matplotlib import pyplot as plt
import re

# Наши модули
from tesseract_utils import get_text_corpus
from recognition_full_name import extract_full_name
from tesseract_utils import get_text_corpus, get_jpg_anon
from office_utils import anonymizer_doc
import pathlib
import numpy as np
from pdf2image import convert_from_path
import os, glob
import uuid
from PIL import Image
import cv2
import zipfile
import thefuzz
from thefuzz import process



current_directory = str(pathlib.Path(__file__).parent.resolve())


def anonymizer_jpg(path_to_img):
    # Получаю объект-картинку, оригинал и копию для аномизации
#     img = plt.imread(path_to_img)
    img = cv2.imread(path_to_img, cv2.IMREAD_GRAYSCALE)
    img_original = img.copy()
    
    # Получаю корпус текста + таблицу координат
    text_corpus, coordinates = get_text_corpus(img)
    
    # Получаю список ФИО
    full_name_list, evals = extract_full_name(text_corpus)
    
    # Получаю таблицу координат NER-объектов
    full_name_coordinates = get_full_name_coordinates(full_name_list, coordinates)
    
    # Получаю анонимизированную картинку
    jpg_anon = get_jpg_anon(img, full_name_coordinates)
    
    # Показать результат
    show_result(img_original, jpg_anon)


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


def show_result(img_original, img_anon):
    print('show_result')
    '''
        Рисует результат
    '''

    fig, axes = plt.subplots(1, 2)

    # Оригинал картинки
    axes[0].imshow(img_original, cmap="gray")
    axes[0].set_title('Оригинальный документ')

    for axis in ['top','bottom','left','right']:
        axes[0].spines[axis].set_linewidth(20)
        axes[0].spines[axis].set_color("whitesmoke")
        axes[0].spines[axis].set_zorder(0)
    axes[0].axes.xaxis.set_visible(False)
    axes[0].axes.yaxis.set_visible(False)

    # Анонимизированная картинки
    axes[1].imshow(img_anon, cmap="gray")
    axes[1].set_title('Анонимизированный документ')

    for axis in ['top','bottom','left','right']:
        axes[1].spines[axis].set_linewidth(20)
        axes[1].spines[axis].set_color("whitesmoke")
        axes[1].spines[axis].set_zorder(0)

    axes[1].axes.xaxis.set_visible(False)
    axes[1].axes.yaxis.set_visible(False)

    # Настроить размер
    fig.set_figwidth(19)    #  ширина и
    fig.set_figheight(12)    #  высота "Figure"
    plt.show() # показать
    
    

    


def pdf_to_img(path):
    img_array_list = []
    images = convert_from_path(path, dpi=300, grayscale=True, fmt='jpeg')
    for image in images:
        image = np.array(image)
#         image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        image = cv2.filter2D(image, -1, kernel)
#         image = cv2.threshold(image, 0,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
#         image = cv2.GaussianBlur(image, (3,3), 0)
#         image = cv2.medianBlur(image, 3)
        img_array_list.append(image)
    return img_array_list


def anonymizer_img(img_as_array):
#     print('anonymizer_img')
    img = img_as_array.copy() # копирую картинку для изменений
    text_corpus, coordinates, metric = get_text_corpus(img)
    print('Длина корпуса:', len(text_corpus))
    full_name_list, evaluation = extract_full_name(text_corpus)
    full_name_coordinates = get_full_name_coordinates(full_name_list, coordinates)
    print('Не найдено имен', len(full_name_list) - len(full_name_coordinates))
    img = np.array(img)
    img_anon = get_jpg_anon(img, full_name_coordinates)
    return img_anon, metric, text_corpus, full_name_list, evaluation


def anonymizer_img_list(img_array_list, name_file='', debug=False):
    if debug:
        os.makedirs(f'{current_directory}/anonimized/{name_file}', exist_ok=True)
        os.makedirs(f'{current_directory}/original/{name_file}', exist_ok=True)
        os.makedirs(f'{current_directory}/tesseract/{name_file}', exist_ok=True)
        os.makedirs(f'{current_directory}/stanza/{name_file}', exist_ok=True)
        os.makedirs(f'{current_directory}/metrics/{name_file}', exist_ok=True)
        
    img_array_list_anon = []
    metrics = []
    evaluations = []
    for num, img in enumerate(img_array_list):
        img_anon, metric, text_corpus, full_name_list, evaluation = anonymizer_img(img)
        img_array_list_anon.append(img_anon)
        metrics.append(metric)
        evaluations.append(evaluation)
        if debug:
            Image.fromarray(img).save(f'{current_directory}/original/{name_file}/page_{str(num)}.jpg', 'JPEG')
            Image.fromarray(img_anon).save(f'{current_directory}/anonimized/{name_file}/page_{str(num)}.jpg', 'JPEG')
            with open(f'{current_directory}/tesseract/{name_file}/page_{str(num)}.txt', 'w') as f:
                f.write(text_corpus)
            with open(f'{current_directory}/stanza/{name_file}/page_{str(num)}.txt', 'w') as f:
                f.write(str(full_name_list))
            with open(f'{current_directory}/metrics/{name_file}/metrics.txt', 'a') as f:
                f.write(f'{metric};{evaluation}\n')
                
    return img_array_list_anon, metrics



def show_result_process(img_array_list, img_array_list_anon):
#     print('show_result_process')
    if len(img_array_list) != len(img_array_list_anon):
        return print('Ошибка: списки картинок не равны')
    for num, img_original in enumerate(img_array_list):
        show_result(img_original, img_array_list_anon[num])
    


def anonymizer(path, debug=False):
    type_file = os.path.splitext(path)[1].lower()
    name_file = os.path.splitext(path)[0]
    if type_file == '.pdf':
        img_array_list = pdf_to_img(path)
        img_array_list_anon, metrics = anonymizer_img_list(img_array_list, name_file, debug=debug)
        path_to_result = img_to_zip(img_array_list_anon, name_file, metrics)
#         show_result_process(img_array_list, img_array_list_anon)
#     elif type_file == '.jpg':
#         anonymizer_jpg(path)
    elif type_file in ['.doc', '.docx', '.xls', '.xlsx', '.rtf', '.txt']:
        img_array_list, img_array_list_anon = anonymizer_doc(path)
        path_to_result = img_to_zip(img_array_list_anon, name_file)
    elif type_file in ['.jpg', '.jpeg', '.png']:
        img_array_list = []
        image = np.array(Image.open(path).convert("RGB"))
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        image = cv2.filter2D(image, -1, kernel)
        img_array_list.append(image)
        img_array_list_anon, metrics = anonymizer_img_list(img_array_list, name_file, debug=debug)
        path_to_result = img_to_zip(img_array_list_anon, name_file, metrics)       
    else:
        print('Ошибка формата:', type_file)
    return path_to_result, img_array_list[0:5], img_array_list_anon[0:5]
        
        
def img_to_zip(img_array_list_anon, name_file, metrics=None):
    os.makedirs(f'{current_directory}/saving_images/{name_file}', exist_ok=True)
    os.makedirs(f'{current_directory}/zip_result/{name_file}', exist_ok=True)
    for num, img in enumerate(img_array_list_anon):
        metric = ''
        if metrics:
            if metrics[num] == 0:
                metric = '_not_sure'
        Image.fromarray(img).save(f'{current_directory}/saving_images/{name_file}/page_{str(num)}{metric}.jpg', 'JPEG')
#             img.save(f'{current_directory}/saving_images/{name_file}/page_' + str(num) + '.jpg', 'JPEG')
    z = zipfile.ZipFile(f'{current_directory}/zip_result/{name_file}.zip', 'w')
    files = [f for f in os.listdir(f'{current_directory}/saving_images/{name_file}/') if os.path.isfile(f'{current_directory}/saving_images/{name_file}/{f}')]
    for file in files:
        z.write(os.path.join(f'{current_directory}/saving_images/{name_file}/{file}'), file)
    z.close()
#     for file in glob.glob(f"{current_directory}/saving_images/*"):
#         os.remove(file)
    return f'zip_result/{name_file}.zip'
        
        



# '''
#     Переписываю под сохранение файлов
# '''

# def convert_to_img_array(path, out_path='input/', dpi=200): #помещает файлы картинок в папку и возвращает их список (каждая страница pdf в отдельном файле)
#     images = convert_from_path(path, dpi=dpi)#, output_folder=path, dpi=300, output_file=str(uuid.uuid4()), use_pdftocairo=True)
#     files = []
#     for i in range(len(images)):
# #         filename = page = os.path.join(out_path, str(uuid.uuid4()) + '.jpg')
# #         images[i].save(filename, 'JPEG')
# #         files.append(str(uuid.uuid4()) + '.jpg')
#         filename = page = os.path.join(out_path, str(i) + '.jpg')
#         images[i].save(filename, 'JPEG')
#         files.append(str(i) + '.jpg')
#     return files
        
    
# def get_anonymizer_img_list(files):
# #     print('anonymizer_process')
#     img_array_list_anon = []
#     for img_path in files:
#         anonymizer_jpg_tmp(img_path)
# #         img_array_list_anon.append(img_anon)
# #     return img_array_list_anon


# def anonymizer_jpg_tmp(path_to_img):
#     # Получаю объект-картинку, оригинал и копию для аномизации
#     img = plt.imread('input/' + path_to_img)
#     img_original = img.copy()
    
#     # Получаю корпус текста + таблицу координат
#     text_corpus, coordinates = get_text_corpus(img)
    
#     # Получаю список ФИО
#     full_name_list = extract_full_name(text_corpus)
    
#     # Получаю таблицу координат NER-объектов
#     full_name_coordinates = get_full_name_coordinates(full_name_list, coordinates)
    
#     # Получаю анонимизированную картинку
#     jpg_anon = get_jpg_anon(img, full_name_coordinates)
    
#     Image.fromarray(jpg_anon).save('output/' + path_to_img, 'JPEG')
    
#     # Показать результат
# #     show_result(img_original, jpg_anon)        
