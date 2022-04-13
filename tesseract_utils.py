#https://colab.research.google.com/drive/1AOkk-TSDFbvCb3Mxb7sTqRMAFbMi6Ra-?usp=sharing#scrollTo=vgZemXj6hejq
#!apt install tesseract-ocr-rus
#!apt install libtesseract-dev
#!pip install pytesseract

import pytesseract
import cv2
import pandas as pd

#Для таблиц
#!!pip install table_ocr
import numpy as np
#from table_ocr.ocr_image import crop_to_text

def tesseract_enabled():
    return 'rus' in pytesseract.get_languages()

#функция слепляет картинки в одну
def concat_images(image_set, how=0):
    def resize_image(image_matrix, nh, nw):
        #image_matrix = crop_to_text(image_matrix)
        oh, ow = image_matrix.shape[:2]
        resized_image = np.full((nh, nw), 1, dtype=image_matrix.dtype)
        resized_image[:oh, :ow] = image_matrix
        return resized_image

    shapes = [imat.shape for imat in image_set]
    max_h = max([s[0] for s in shapes])
    max_w = max([s[1] for s in shapes])
    images_resized = [
            resize_image(img, max_h, max_w) 
            for img in image_set
        ]
    if (how == 0) or (how == 'vertical'):
        concats = cv2.vconcat(images_resized)
    elif (how == 1) or (how == 'horizontal'):
        concats = cv2.hconcat(images_resized)
    else:
        concats = cv2.hconcat(images_resized)
    return concats



def get_text_corpus(jpg):
    if not tesseract_enabled():
        raise Exception('Russian is not installed..')
        
    data = pytesseract.image_to_data(jpg, output_type='data.frame', lang='rus', config='hocr')
    median = data[data['conf'] > 0]['conf'].median()
    data = data[~pd.isna(data.text)]
    
    if median >= 95:
        metrics = 1
    else:
        metrics = 0
        
    if len(data) < 1:
        #raise Exception('No words..')
        print('No words..')
        return '', None, None
    try:
        return data.text.str.cat(sep=' '), data, metrics
    except:
        return ' '.join(data['text'].astype('str')), data, metrics     


def get_jpg_anon(jpg, coordinates, filled=True):
    '''
    # Функция принимает картинку, список имен, возвращает картинку с закрашенными
    # plt.imshow(get_jpg_anon(img, coord))
    '''
    if filled:
        filled = -1
    else:
        filled = 2
    
    if isinstance(coordinates, pd.DataFrame): #добавил это условие, потом что иногда пустые координаты могут приходить
        for item in coordinates.iterrows():
            c = item[1]
            jpg = cv2.rectangle(jpg, (c.left, c.top), (c.left + c.width, c.top + c.height), (0, 0, 0), filled) #black
            
    return jpg

    
