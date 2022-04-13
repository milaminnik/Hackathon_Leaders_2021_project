from matplotlib import pyplot as plt
import re

# Наши модули
from recognition_full_name import extract_full_name
from utils import get_full_name_coordinates
from tesseract_utils import get_text_corpus, get_jpg_anon
from office_utils import anonymizer_doc
from tables import anonymizer_table

import pathlib
import numpy as np
from pdf2image import convert_from_path
import os
import uuid
from PIL import Image
import cv2
import zipfile
import thefuzz
from thefuzz import process
import pandas as pd
import shutil
import tempfile



current_directory = str(pathlib.Path(__file__).parent.resolve())

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
    for num, image in enumerate(images):
        image = np.array(image)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        image = cv2.filter2D(image, -1, kernel)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.threshold(image, 0,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        img_array_list.append(image)
    return img_array_list



def anonymizer_img(img_as_array):
    img = img_as_array.copy() # копирую картинку для изменений
    
    # Корпус текста
    text_corpus, coordinates, metric = get_text_corpus(img)
    
    # Список ФИО
    full_name_list, evaluation = extract_full_name(text_corpus)
    
    # Таблица координат ФИО
    full_name_coordinates = get_full_name_coordinates(full_name_list.copy(), coordinates)
    
    img = np.array(img)
    img_anon = get_jpg_anon(img, full_name_coordinates)
    
    tolist = full_name_coordinates
    if isinstance(full_name_coordinates, pd.DataFrame):
        if 'text' in full_name_coordinates:
            tolist = full_name_coordinates['text'].tolist()
    
    return img_anon, metric, text_corpus, full_name_list, tolist, evaluation


def anonymizer_img_list(img_array_list, name_file='', debug=False, test_dir=None):

    if debug:
        os.makedirs(f'{test_dir}/anonimized/{doc_type}/{name_file}', exist_ok=True)
        os.makedirs(f'{test_dir}/original/{doc_type}/{name_file}', exist_ok=True)
        
    img_array_list_anon = []
    metrics = []
    evaluations = []
    for num, img in enumerate(img_array_list):
        img_anon, metric, text_corpus, full_name_list, full_name_list_clear, evaluation = anonymizer_table(img) #anonymizer_img(img)
        img_array_list_anon.append(img_anon)
        metrics.append(metric)
        evaluations.append(evaluation)
        if debug:
            img_origin_path_save = f'{test_dir}/original/{doc_type}/{name_file}/page_{str(num)}.jpg'
            img_anon_path_save = f'{test_dir}/anonimized/{doc_type}/{name_file}/page_{str(num)}.jpg'
            Image.fromarray(img).save(img_origin_path_save, 'JPEG')
            Image.fromarray(img_anon).save(img_anon_path_save, 'JPEG')
            with open(f'{test_dir}/testsample_2.csv', 'a') as f:
                f.write(f'"{img_origin_path_save}";"{img_anon_path_save}";"{text_corpus.replace(";", ":")}";"{str(full_name_list).replace(";", ":")}";{metric};{evaluation};;;{doc_type};;{str(full_name_list_clear).replace(";", ":")}\n')

    return img_array_list_anon, metrics



def show_result_process(img_array_list, img_array_list_anon):
    if len(img_array_list) != len(img_array_list_anon):
        return print('Ошибка: списки картинок не равны')
    for num, img_original in enumerate(img_array_list):
        show_result(img_original, img_array_list_anon[num])

        
        
def proc_arc(path, debug=False, result_dir=None, test_dir=None):
    name_file, _ = os.path.splitext(os.path.basename(path))

    if os.path.isfile(path):
        try:
            done_list = []
            with tempfile.TemporaryDirectory() as tmppath: #временная папка удаляется при выходе из контекста
                with zipfile.ZipFile(path, 'r') as z:
                    file_list = []
                    for file in z.namelist():
                        if not os.path.isdir(file):
                            z.extract(file, tmppath)
                            file_list.append(os.path.join(tmppath, file))
                    z.close()
                    
                for file in file_list:
                    try:
                        print('Work with: ' + file)
                        out, _, _ = anonymizer(file, debug=debug, result_dir=result_dir, test_dir=test_dir)
                        if out:
                            done_list.append(out)
                    except Exception as e:
                        print('for file in file_list: ' + str(e))
                
                path_to_result = f'{result_dir}/zip_result/{name_file}.zip'
                with zipfile.ZipFile(path_to_result, 'w') as z:
                    for file in done_list:
                        z.write(file, os.path.basename(file))
                    z.close()              
            return path_to_result 
        except Exception as e:
            print('proc_arc: ' + str(e))
    else:
        print(path + ' is not file!')

      

def anonymizer(path, debug=False, result_dir=None, test_dir=None):
    
    if not result_dir:
        result_dir = current_directory
    if not test_dir:
        test_dir = current_directory
    
    path_to_result = ''
    img_array_list = []
    img_array_list_anon = []  
        
    name_file, type_file = os.path.splitext(os.path.basename(path))
    
    type_file = type_file.lower()
    
    if type_file == '.zip':
        return proc_arc(path, debug=debug, result_dir=result_dir, test_dir=test_dir), img_array_list, img_array_list_anon
    
    if type_file == '.pdf':
        img_array_list = pdf_to_img(path)
        img_array_list_anon, metrics = anonymizer_img_list(img_array_list, name_file, debug=debug, test_dir=test_dir)
        path_to_result = img_to_zip(img_array_list_anon, name_file, metrics, result_dir=result_dir)
        #show_result_process(img_array_list, img_array_list_anon)
    elif type_file in ['.doc', '.docx', '.xls', '.xlsx', '.rtf', '.txt']:
        img_array_list, img_array_list_anon = anonymizer_doc(path, debug=debug, test_dir=test_dir)
        path_to_result = img_to_zip(img_array_list_anon, name_file, result_dir=result_dir)
    elif type_file in ['.jpg', '.jpeg', '.png']:
        img_array_list = []
        image = np.array(Image.open(path).convert("RGB"))
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        image = cv2.filter2D(image, -1, kernel)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.threshold(image, 0,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        img_array_list.append(image)
        img_array_list_anon, metrics = anonymizer_img_list(img_array_list, name_file, debug=debug, test_dir=test_dir)
        path_to_result = img_to_zip(img_array_list_anon, name_file, metrics, result_dir=result_dir)       
    else:
        print('Ошибка формата:', type_file)
            
    return path_to_result, img_array_list, img_array_list_anon


        
def img_to_zip(img_array_list_anon, name_file, metrics=None, result_dir=None):
    if not result_dir:
        result_dir = current_directory
    
    saving_images = os.path.join(result_dir, 'saving_images', name_file)
    result = os.path.join(result_dir, 'zip_result')
    os.makedirs(saving_images, exist_ok=True)
    os.makedirs(result, exist_ok=True)
    
    for num, img in enumerate(img_array_list_anon):
        metric = ''
        if metrics:
            if metrics[num] == 0:
                metric = '_not_sure'
        #Image.fromarray(img).save(f'{result_dir}/saving_images/{name_file}/page_{str(num)}{metric}.jpg', 'JPEG')
        Image.fromarray(img).save(os.path.join(saving_images, f'page_{str(num)}{metric}.jpg'), 'JPEG')
    
    result = os.path.join(result, f'{name_file}.zip')
    files = [f for f in os.listdir(saving_images) if os.path.isfile(os.path.join(saving_images, f))]
    with zipfile.ZipFile(result, 'w') as z:
        for file in files:
            z.write(os.path.join(saving_images, file), file)
        z.close()

    shutil.rmtree(saving_images, ignore_errors=True)
    return result 
 
