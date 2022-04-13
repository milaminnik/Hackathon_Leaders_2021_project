import streamlit as st
import pandas as pd
import os
import shutil

from engine import anonymizer
    
st.markdown(''' <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}d
</style> ''', unsafe_allow_html=True)

st.sidebar.header('Загрузите файл:')

file_upload = st.sidebar.file_uploader('См. допустимые форматы', type=['xls', 'xlsx', 'pdf', 'doc', 'docx', 'rtf', 'jpg'])


if file_upload:
    if st.sidebar.button('Анонимизировать'):
        with open(file_upload.name, "wb") as f: 
            f.write(file_upload.getbuffer())
        os.makedirs('saving_images', exist_ok=True)
        os.makedirs('zip_result', exist_ok=True)
        zip_down, default_image, result_image = anonymizer(file_upload.name)

        with open(os.path.join('zip_result', str(file_upload.name.rsplit(".", 1)[0]))+'.zip', 'rb') as f1:
            #os.system(f'rm {os.path.join('zip_result', 'tmp.py')}')
            st.download_button('Скачать анонимизированные файлы (zip)', f1, file_name = f'{file_upload.name.split(".", -1)[0]}_anonymized.zip') 

        os.system(f'rm {file_upload.name}')

        col1, col2 = st.columns(2)
        col1.markdown('### Исходник:')
        col1.image(default_image)
        col2.markdown('### Аноним:')
        col2.image(result_image)





  


