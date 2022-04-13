#Для ковертера
#!!add-apt-repository ppa:libreoffice/ppa && sudo apt-get update
#!!apt-get install unoconv

#Для анонимайзера
#!!pip install --upgrade --force-reinstall fitz
#!!pip install --upgrade --force-reinstall pymupdf
#!!pip install webcolors

#Для конвертера pdf2jpg
#!apt-get install poppler-utils
#!pip install pdf2image

#Тексттрак
#!pip install textract

import textract

import os
import tempfile
import fitz
from webcolors import name_to_rgb

import subprocess
import sys
import re

from pdf2image import convert_from_path
import uuid
import os
import numpy as np

import warnings

from recognition_full_name import extract_full_name
#from tesseract_utils import get_text_corpus_doc
#from engine import pdf_to_img
#from engine import anonymizer_img_list


#def convert_to_pdf(in_file, path=''): #помещает файл с тем же именем, но новым расширением pdf в папку
#        args = ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', path, in_file]
#        process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=None)
#        #print(process.stdout.decode())
#        filename = re.search('-> (.pdf) using filter', process.stdout.decode())
#        return filename is None


#def convert_to_jpg(in_file, out_path='', dpi=300): #помещает файлы картинок в папку и возвращает их список (каждая страница pdf в отдельном файле)
#        images = convert_from_path(in_file, dpi=dpi)#, output_folder=path, dpi=300, output_file=str(uuid.uuid4()), use_pdftocairo=True)
#        files = []
#        for i in range(len(images)):
#            filename = page = os.path.join(out_path, str(uuid.uuid4())+'.jpg')
#            images[i].save(filename, 'JPEG')
#            files.append(filename)
#        return files


#def anonymize_pdf(in_file, out_file, text, color='green', filled=True): #создаёт новый файл pdf
#        pix = fitz.Pixmap(fitz.csRGB, (0, 0, 300, 300), 0) #просто создается картинка, которая затем помещается на текст
#        pix.set_rect(pix.irect, name_to_rgb(color)) #поэтому лучше это вынестив инициализацию, чтобы не плодить сущности
#        doc = fitz.open(in_file)
#        for page in doc:
#            text_instances = page.search_for(text) #ищет все совпадение и для каждого использует маркер
#            for inst in text_instances:
#                highlight = page.add_highlight_annot(inst)
#                page.insert_image(highlight.rect, pixmap=pix, keep_proportion=False, overlay=filled) #помещает на каждый мркер картинку
#        doc.save(out_file, garbage=4, deflate=True, clean=True)
#        return os.path.exists(out_file)


def _anonymize_pdf(in_file, out_file, substring_list, color='green', filled=True): #создаёт новый файл pdf
        pix = fitz.Pixmap(fitz.csRGB, (0, 0, 300, 300), 0) #просто создается картинка, которая затем помещается на текст
        pix.set_rect(pix.irect, name_to_rgb(color)) #поэтому лучше это вынестив инициализацию, чтобы не плодить сущности
        doc = fitz.open(in_file)
        for substring in substring_list:
          if len(substring) > 0:
            for page in doc:
                text_instances = page.search_for(substring) #ищет все совпадение и для каждого использует маркер
                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    page.insert_image(highlight.rect, pixmap=pix, keep_proportion=False, overlay=filled) #помещает на каждый мркер картинку
        doc.save(out_file, garbage=4, deflate=True, clean=True)
        return os.path.exists(out_file)


def _convert_to_pdf(in_file, path=''): #помещает файл с тем же именем, но новым расширением pdf в папку
        filename = os.path.basename(in_file)
        name, _ = os.path.splitext(filename)
        args = ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', path, in_file]
        process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=None)
        print(process.stdout.decode())
        pdf = os.path.join(path, name + '.pdf')
        return os.path.exists(pdf), pdf


def _convert_to_jpg(in_file, dpi=300):
        #return convert_from_path(in_file, dpi=dpi, fmt='jpeg')
        images = convert_from_path(in_file, dpi=dpi, fmt='jpeg')
        images_list = []
        for img in images:
                images_list.append(np.array(img))
        return images_list


def anonymizer_doc(path, debug=False, test_dir=None):
    #return proccess_doc(path) #переводит doc->pdf->jpg и дальше по основной ветке
    return proccess_docfile(path, color='black', filled=True, dpi=200)  


def proccess_docfile(in_file, color='green', filled=True, dpi=300):
    #всякие проверки
    if not os.path.exists(in_file):
      raise Exception('No file exist..')

    #if not substring_list:
    #  raise Exception('No substrings in list..')

    _, ext = os.path.splitext(os.path.basename(in_file))
    if not ext.lower() in ['.doc', '.docx', '.xls', '.xlsx', '.rtf', '.txt']:
      warnings.warn(f'{ext} - Inappropriate file format.')
      #print('Inappropriate file format')
      return

    #Процесс пошёл..
    with tempfile.TemporaryDirectory() as tmppath: #временная папка удаляется при выходе из контекста
      ok, old_pdf = _convert_to_pdf(in_file, tmppath)  
      if ok: 
        corpus = textract.process(old_pdf, language='rus').decode("utf-8") 
        name_list, _ = extract_full_name(corpus)
        new_pdf = os.path.join(tmppath, str(uuid.uuid4()) + '.pdf')
        if _anonymize_pdf(old_pdf, new_pdf, substring_list=name_list, color=color, filled=filled): 
          return _convert_to_jpg(old_pdf, dpi=dpi), _convert_to_jpg(new_pdf, dpi=dpi)
      else:
        raise Exception('convert_to_pdf error')
       

#def proccess_doc(in_file, color='green', filled=True, dpi=300):
#    #всякие проверки
#    if not os.path.exists(in_file):
#      raise Exception('No file exist..')
#
#    #if not substring_list:
#    #  raise Exception('No substrings in list..')#
#
#    _, ext = os.path.splitext(os.path.basename(in_file))
#    if not ext.lower() in ['.doc', '.docx', '.xls', '.xlsx', '.rtf', '.txt']:
#      warnings.warn(f'{ext} - Inappropriate file format.')
#      #print('Inappropriate file format')
#      return
#
#    #Процесс пошёл..
#    with tempfile.TemporaryDirectory() as tmppath: #временная папка удаляется при выходе из контекста
#      ok, old_pdf = _convert_to_pdf(in_file, tmppath)  
#      if ok:
#        img_array_list = pdf_to_img(old_pdf)
#        img_array_list_anon = anonymizer_img_list(img_array_list)
#        return img_array_list_anon
#      else:
#        raise Exception('convert_to_pdf error')
