import re
import pandas as pd


from django.conf import settings


global re_date, re_university, months_shkt
re_date = r'([a-z]+\s?)?\d{4}\s?((?P<sep>(-|to|–))\s?((([a-z]+\s?)?\d{4})|present))?'

months_shkt = ['jan', 'feb', 'mar', 'march', 'apr', 'april', 'may', 'jun', 'june', 'jul', 'july', 'aug', 'august', 'nov', 'sep', 'sept', 'oct', 'dec']


class ExperienceParser():
    
    def __init__(self, text):
        self.text = text.replace('\n', ' ').replace(',', ' ')
        self.slots_date = {}
        self.slots_position = {}
    

    def fill_slots_date(self):
        for date in re.finditer(re_date, self.text, re.I):
            for mon in months_shkt:
                if date.group(0).lower().startswith(mon):
                    break
            else:
                date = re.search(r'\d{2,4}\s?((?P<sep>(-|to|–))\s?((([a-z]+\s?)?\d{2,4})|present))?', date.group(0))
            self.slots_date[self.text.find(date.group(0))] = {'date':date.group(0)}

    

    def fill_slots_position(self):
        df = pd.read_csv(settings.BASE_DIR+"/engine/core/corpus/exp_position.csv", header=None)
        df[0] = df[0].apply(lambda x: x.lower())
        positions = df[0].tolist()

        for pos in positions:
            for found_pos in re.finditer(pos, self.text, re.I):
                self.slots_position[self.text.find(found_pos.group(0))] = {'position':pos.title()}
                self.text = self.text.replace(found_pos.group(0), " ", 1)

    def get_all_data(self):
        self.fill_slots_date()
        self.fill_slots_position()

        emp_slots_max = max(len(self.slots_date), len(self.slots_position))
        emp_sub_block = [[] for i in range(emp_slots_max)]
        counter = 0
        for i in range(emp_slots_max):
            emp_sub_block[counter] = {}
            if i<len(self.slots_date):
                emp_sub_block[counter]['date'] = self.slots_date[list(sorted(self.slots_date))[i]]['date']
            if i<len(self.slots_position):
                emp_sub_block[counter]['position'] = self.slots_position[list(sorted(self.slots_position))[i]]['position']
            counter+=1
        

        return emp_sub_block