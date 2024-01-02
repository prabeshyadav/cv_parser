import re
import pandas as pd


from django.conf import settings


global re_date, re_university, months_shkt
re_date = r'([a-z]+\s?)?\d{4}\s?((?P<sep>(-|to|–))\s?((([a-z]+\s?)?\d{4})|present))?'
re_university = r'([a-z]+\s)?university(\sof\s[a-z]+)?'

months_shkt = ['jan', 'feb', 'mar', 'march', 'apr', 'april', 'may', 'jun', 'june', 'jul', 'july', 'aug', 'august', 'nov', 'sep', 'sept', 'oct', 'dec']



class EducationParser():
    #global self.slots_date, self.slots_univ, self.slots_degree, self.slots_grade
    

    def __init__(self, text):
        self.text = text.replace('\n', ' ').replace(',', ' ')
        self.slots_date = {}
        self.slots_univ = {}
        self.slots_degree = {}
        self.slots_grade = {}


    def fill_slots_date(self):
        for date in re.finditer(re_date, self.text, re.I):
            for mon in months_shkt:
                if date.group(0).lower().startswith(mon):
                    break
            else:
                date = re.search(r'\d{2,4}\s?((?P<sep>(-|to|–))\s?((([a-z]+\s?)?\d{2,4})|present))?', date.group(0))
            self.slots_date[self.text.find(date.group(0))] = {'date':date.group(0)}

    

    def fill_slots_univ(self):
        for univ in re.finditer(re_university, self.text, re.I):
            self.slots_univ[self.text.find(univ.group(0))] = {'university':univ.group(0)}


    def fill_slots_degree(self):
        df = pd.read_csv(settings.BASE_DIR+'/engine/core/corpus/education.csv', header=None)
        degrees = df[0].tolist()

        for deg in degrees:
            re_deg = r'\s'+deg+'\s?(in\s[a-z]+|\([a-z]+\))?\s'
            for degree in re.finditer(re_deg, self.text, re.I):
                self.slots_degree[self.text.find(degree.group(0))] = {'degree':degree.group(0)}
        

    def fill_slots_grade(self):
        for grade in re.finditer(r'(\d{1,2}\.\d{1,4}?%|[1-4]\.(\d{1,2})?)', self.text, re.I):
            self.slots_grade[self.text.find(grade.group(0))] = {'grade':grade.group(0)}

    


    def get_all_data(self):
        self.fill_slots_date()
        self.fill_slots_univ()
        self.fill_slots_degree()
        self.fill_slots_grade()

        edu_slots_max = max(len(self.slots_date), len(self.slots_univ), len(self.slots_degree), len(self.slots_grade))
        edu_sub_block = [[] for i in range(edu_slots_max)]
        counter = 0
        for i in range(edu_slots_max):
            edu_sub_block[counter] = {}
            if i<len(self.slots_date):
                edu_sub_block[counter]['date'] = self.slots_date[list(sorted(self.slots_date))[i]]['date']
            if i<len(self.slots_univ):
                edu_sub_block[counter]['university'] = self.slots_univ[list(sorted(self.slots_univ))[i]]['university']
            if i<len(self.slots_degree):
                edu_sub_block[counter]['degree'] = self.slots_degree[list(sorted(self.slots_degree))[i]]['degree']
            if i<len(self.slots_grade):
                edu_sub_block[counter]['grade'] = self.slots_grade[list(sorted(self.slots_grade))[i]]['grade']
            counter+=1
            
        return edu_sub_block
    
