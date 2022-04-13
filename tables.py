import pytesseract
import cv2
import pandas as pd
import numpy as np

from recognition_full_name import extract_full_name
from tesseract_utils import get_text_corpus, get_jpg_anon, concat_images
from utils import get_full_name_coordinates

import itertools
from table_ocr.extract_tables import find_tables
from table_ocr.extract_cells import extract_cell_images_from_table
#from table_ocr.ocr_image import crop_to_text



def anonymizer_table(img_as_array, work_with_table=True, anonimize_whole_column=False, treshhold=0.5):
    img = img_as_array.copy()
    text_corpus, coordinates, metric = get_text_corpus(img)

    appendix = ''
    whole_column = ''
    appendix_name_list = []
    if work_with_table:
        try:
            #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
            tables = find_tables(img)
            if tables:
                for _, table in enumerate(tables):
                    cells = extract_cell_images_from_table(table)
                    flattened = list(itertools.chain.from_iterable(cells))
                    col_count = len(cells[0])
                    for i in range(col_count):
                        col = flattened[i::col_count]
                        combined = concat_images(col)
                        whole_column = pytesseract.image_to_string(combined, lang='rus', config='hocr').replace("\n", " ")
                        if anonimize_whole_column:
                            name_list, _ = extract_full_name(whole_column)
                            if treshhold:
                                if len(' '.join(name_list)) / len(whole_column) >= treshhold:
                                    appendix_name_list = appendix_name_list + [i for i in whole_column.split(' ') if len(i) > 2]
                                    appendix = appendix + whole_column
                                    break
                        appendix = appendix + whole_column
        except Exception as e:
            print(e)
        if (work_with_table) and (len(appendix) > 0):
            text_corpus = text_corpus + " APPENDIX: " + appendix
          
    full_name_list, evaluation = extract_full_name(text_corpus)

    full_name_list = list(set(full_name_list + appendix_name_list))
    #print(appendix_name_list)
    #print(full_name_list)
    #print(text_corpus)
    
    full_name_coordinates = get_full_name_coordinates(full_name_list.copy(), coordinates)
    img = np.array(img)
    img_anon = get_jpg_anon(img, full_name_coordinates)
    
    tolist = full_name_coordinates
    if isinstance(full_name_coordinates, pd.DataFrame):
        if 'text' in full_name_coordinates:
            tolist = full_name_coordinates['text'].tolist()
    
    return img_anon, metric, text_corpus, full_name_list, tolist, evaluation


