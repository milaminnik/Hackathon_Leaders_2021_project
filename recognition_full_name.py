import stanza
stanza.download('ru')

import re
import json
import os
import pathlib


current_directory = str(pathlib.Path(__file__).parent.resolve())
with open(pathlib.Path(f'{current_directory}/ner_exceptions.json'), 'r') as file:
    exceptions_dict = json.load(file)


def extract_full_name(corpus):
    
    corpus = preprocess_text(corpus)    
    result = stanza_process(corpus)    
    result = first_postprocess(result)
    
    eval_marks = []
    full_name_list = []
    for name in result:
        if re.findall(r'[А-Я]{1}\.{1}\s*[А-Я]{1}\.{1}\s*[А-Я]{1}[А-Я|а-я]+|[А-Я]{1}[А-Я|а-я]+\s+[А-Я]\.{1}\s*[А-Я]\.{1}',\
                      str(name)) != []: # регулярка для поиска имен с инициалами
            
            if filter_result(name, 'initials'):
                
                # если пробела между инициалами и фамилией нет
                if re.findall(r'[А-Я]{1}\.{1}\s*[А-Я]{1}\.{1}[А-Я]{1}[А-Я|а-я]+', str(name)) != []:
                    full_name_list.append(str(name).strip())
                
                # если есть пробел
                else:
                    first_name = re.findall(r'[А-Я]{1}\.{1}\s*[А-Я]{1}\.{1}', str(name))
                    second_name = name.replace(first_name[0], '')
                    second_name = second_name.split(' ')
                        
                    if first_name != []:
                        full_name_list.append(first_name[0].strip())
                        for name_ in second_name:
                            full_name_list.append(str(name_).strip())
                        
                    else:
                        name_tmp = re.split(' ', str(name))
                        for name_ in name_tmp:
                            full_name_list.append(str(name_).strip())
                
                eval_marks.append(0)
                
        else:                           # если полное фио
            if filter_result(name, 'full'):
                
                eval_marks.append(get_evaluation(name, result))
                
                new_name = re.split(' ', str(name))

                for name_ in new_name:
                    full_name_list.append(str(name_).strip())
                    
    
    if set(eval_marks) == {0}:
        evaluation = 0
    else:
        evaluation = 1
            
    full_name_list = second_postprocess(full_name_list)        
    
    return full_name_list, evaluation  # evaluation : 0 = уверенность, 1 = могут быть ошибки
    

def preprocess_text(corpus):
    
    ''' Предобработка '''
    
    new_c = re.sub('[$|@|&|"|||:|#|>|<|„|“|^]', '', corpus)
    new_c = new_c.replace('\n\n', ', ')
    new_c = new_c.replace('\n', ' ')
    new_c = new_c.replace('  ', ' ')
    new_c = re.sub(r'\d+', '', new_c)
    new_c = re.sub(r'\s{1}\W{1}\s{1}', ' ', new_c)
    new_c = new_c.replace('  ', ' ')
    
    corpus_list = new_c.split(' ')
    
    new_corpus_list = []
    for n, elem in enumerate(corpus_list):
        
        if n != len(corpus_list) - 1 and len(elem) >= 2 and elem[-1] == '-' and re.findall(r'[А-Я]{1}', corpus_list[n+1]) == []:
            elem = elem.replace('-', '') + corpus_list[n+1]
            corpus_list.pop(n+1)
            
        elif n != len(corpus_list) - 1 and len(elem) >=3 and elem[-1] == ',' and elem[-2] == '-' and re.findall(r'[А-Я]{1}', corpus_list[n+1]) == []:
            elem = elem.replace('-', '')
            elem = elem.replace(',', '') + corpus_list[n+1]
            corpus_list.pop(n+1)
            
        elif n != len(corpus_list) - 1 and len(elem) >= 2 and elem[-1] == '-' and re.findall(r'[А-Я]{1}', corpus_list[n+1]) != []:
            elem = elem.replace('-', '')
        
        new_corpus_list.append(elem)
    
    corpus_str = ' '.join(new_corpus_list)
    
    return corpus_str.strip()

    
def stanza_process(corpus):
    
    ''' Выявление ФИО '''
    
    nlp = stanza.Pipeline(lang='ru', processors='tokenize,ner', verbose=False)
    doc = nlp(corpus)
    result = [ent.text for ent in doc.ents if ent.type == 'PER']
    return result
    

def get_evaluation(entity, result_list):
    
    ''' Оценка уверенности '''
    
    reg_full = r'[А-Я]{1}[а-я|А-Я]+\s{1}[А-Я]{1}[а-я|А-Я]+\s{1}[А-Я]{1}[а-я|А-Я]+' # регулярка для полных ФИО
    reg_two_full = r'[А-Я]{1}[а-я|А-Я]+\s{1}[А-Я]{1}[а-я|А-Я]+'                    # регулярка для имени и отчества
    reg_one_name = r'[А-Я]{1}[а-я|А-Я]+'                                           # регулярка для отдельного слова
    
    # если полное ФИО
    if re.findall(reg_full, str(entity)) != []:
        return 0
    
    # если отдельно фамилия
    elif len(entity.split(' ')) == 1 and re.findall(reg_one_name, str(entity)) != [] and result_list[-1] != entity:
        
        entity_position = result_list.index(entity)
        next_entity = result_list[entity_position + 1]
        
        if len(next_entity.split(' ')) == 2 and re.findall(reg_two_full, str(next_entity)) != [] and re.findall(r'[А-Я]{1}\.{1}\s*[А-Я|а-я]+',\
                                                                                                                str(next_entity)) == []:
            return 0
        else:
            return 1
    
    # если два слова - имя и отчество
    elif len(entity.split(' ')) == 2 and re.findall(reg_two_full, str(entity)) != [] and result_list[0] != entity:
        
        entity_position = result_list.index(entity)
        previous_entity = result_list[entity_position - 1]
        
        if len(previous_entity.split(' ')) == 1 and re.findall(reg_one_name, str(previous_entity)) != [] and re.findall(r'[А-Я]{1}\.{1}\s*[А-Я|а-я]+',\
                                                                                                                        str(previous_entity)) == []:
            return 0
        else:
            return 1                                                                                                                
     
    else:
        return 1


def filter_result(entity, name_type):
    
    ''' Фильтр стоп-слов '''
    
    if name_type == 'initials':
        tmp_entity = entity.lower().strip()
        tmp_entity = tmp_entity.replace(' ', '')
        if tmp_entity in exceptions_dict['initials']:
            return False
        else:
            return True
       
    elif name_type == 'full':
        tmp_entity = entity.lower().strip()
        if tmp_entity in exceptions_dict['full']:
            return False
        else:
            return True
        
    elif name_type == 'other':
        tmp_entity = entity.lower().strip()
        if tmp_entity in exceptions_dict['other']:
            return False
        else:
            return True    

        
def first_postprocess(raw_result):
    
    ''' Пост-обработка 1 '''
    
    raw_result = list(filter(None, raw_result))
    
    new_result = []
    for elem in raw_result:
        if elem[0].islower():
            continue
        
        if len(elem) < 3:
            continue
        elif len(elem) == 3 and re.findall(r'[А-Я]{3}', str(elem)) != []:
            continue
        else:
            new_result.append(elem)
    
    return new_result

        
def second_postprocess(old_list):
    
    ''' Пост-обработка 2 '''
    
    new_list = []
    for elem in old_list:
        if len(elem) < 3:
            continue
        elif len(elem) == 3 and re.findall(r'[А-Я]{3}', str(elem)) != []:
            continue
            
        if ' ' in elem and re.findall(r'\s+[А-Я]{1}\.{1}\s*[А-Я]{1}\.{1}\s+|[А-Я]{1}\.{1}\s*[А-Я]{1}\.{1}\s+[А-Я|а-я]+\s+|[А-Я|а-я]+\s+[А-Я|а-я]+\s+[А-Я]{1}\.{1}\s*[А-Я]{1}\.{1}', str(elem)) != []:
            elem_tmp = elem.split(' ')
            for elem_ in elem_tmp:
                if filter_result(elem_, 'other'):
                    new_list.append(elem_)
        
        elif filter_result(elem, 'other'):
            new_list.append(elem)
    
    return new_list



#    Copyright 2021 leaders_liga

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
