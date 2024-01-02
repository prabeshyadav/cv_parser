import fitz, docxpy
import re, os
import pandas as pd
from django.conf import settings
from engine.core.personal_data_parser import PersonalParser, PersonalParserColon
from engine.core.edu_parser import EducationParser
from engine.core.exp_parser import ExperienceParser
from engine.core.training_parser import TrainingParser


global _headings, headings, personal_sub, invalid_chars

_headings = {
                'objective': ['objective', 'summary', 'personal profile'],
                'personal': ['personal details', 'personal data'],
                'education': ['education', 'education details', 'education and qualifications'],
                'skills': ['skills','technical skills', 'computer skills', 'selected skills', 'it skills'],
                'interests and hobbies': ['interests and hobbies', 'interests', 'personal interests'],
                'projects': ['projects', 'projects accomplished'],
                'experience': ['experience', 'work history', 'employment', 'occupation', 'employment history', 'professional experience', 'working experience'],
                'trainings': ['trainings', 'training and professional development', 'professional development'],
                'web links': ['web links'],
                'awards and achievements': ['awards and achievements', 'awards', 'achievements'],
                'references': ['references'],
                'languages': ['languages', 'language skills'],
            }

headings = {}


institute_type = {'school','college','campus','institute'}

invalid_chars = ['•']


class CVParser():

    def __init__(self, file):
        CVParser.flat_headings()
        self.user_headings = dict()
        # extract text from pdf
        if file.split('.')[1].lower() == 'pdf':
            self.text = self.extract_text_pdf(file)
        elif file.split('.')[1].lower() == 'docx':
            self.text = self.extract_text_docx(file)
        self.text_line =  self.text.split('\n')
        # extract all headings with its content {'heading':'heading_content'}
        self.heading_blocks = self.extract_heading_blocks()



    @staticmethod
    def flat_headings():
        for key, values in _headings.items():
            for v in values:
                headings[v] = key
    
    
    @property
    def parsed_data(self):
        parsed_data = {}
        parsed_data['personal'] = self.extract_personal_info()
        parsed_data['objective'] = self.extract_objective()
        parsed_data['skills'] = self.extract_skills()
        parsed_data['education'] = self.extract_edu_info()
        parsed_data['experience'] = self.extract_exp_info()
        parsed_data['trainings'] = self.extract_training_info()
        return parsed_data        


    def extract_text_docx(self, file):
        text = docxpy.process(file)

        text = re.sub(' +',' ', text)
        return text

    def extract_text_pdf(self, file):
        doc = fitz.open(file)
        text = ''

        ## extract all text
        for i in range(doc.page_count):
                text += doc[i].get_text("text")

        #remove invalid characters
        # for i in invalid_chars:
        #     text = text.replace(i, '')
        
        text = re.sub(' +',' ', text)
        return text
        

    def extract_heading(self, line):
        if line.lower().strip() in headings:
            _heading = line.lower()
            self.user_headings[headings[_heading.strip()]] = _heading
            return _heading
        else:
            return False

    

    def find_headings(self):
        found_headings = []
        for line in self.text_line:
            # remove colons if it exist and check for heading
            if ':' in line:
                filter_line = line.split(':')[0].strip()
            else:
                filter_line = line.replace(':',' ').strip()
            _heading = self.extract_heading(filter_line)
            if _heading:
                found_headings.append(_heading)
        return found_headings


    def extract_heading_blocks(self):
        found_headings = self.find_headings()
        heading_blocks = {}
        found_block_pos_min = len(self.text)
        for i in range(len(found_headings)):
            
            # for personal details block seperation that usually do not have heading
            if self.text.lower().find(found_headings[i])<found_block_pos_min:
                found_block_pos_min = self.text.lower().find(found_headings[i])


            start = self.text.lower().find(found_headings[i])+len(found_headings[i])
            
            if i == len(found_headings)-1:
                end = len(self.text)
            else:
                end = self.text.lower().find(found_headings[i+1])
            heading_blocks[found_headings[i]] = self.text[start:end].lstrip(':')

        if found_block_pos_min != 0 and 'personal' not in self.user_headings:
            self.user_headings['personal'] = 'personal'
            heading_blocks['personal'] = self.text[:found_block_pos_min]
        
        # for i,j in heading_blocks.items():
        #     print(i,j)
        #     print()
        #print(heading_blocks)
        return heading_blocks
    
    @staticmethod
    def is_text_seperated(text):        # is each line seperated by colon or -
        colon_count = 0
        for i in text:
            if i==':': colon_count += 1
        if colon_count/len(text) >= 0.01:
            return True
        else:
            return False


    def extract_personal_info(self):
        if 'personal' in self.user_headings:
            personal_block = self.heading_blocks[self.user_headings['personal']]
            #print(repr(personal_block))
            if CVParser.is_text_seperated(personal_block):
                _personal = PersonalParserColon(personal_block)
            else:
                _personal = PersonalParser(personal_block)
            personal = _personal.get_all_data()
            return personal
        else:
            return None
    

    def extract_edu_info(self):
        if 'education' in self.user_headings:
            edu_block = self.heading_blocks[self.user_headings['education']]
            education = EducationParser(edu_block)
            return education.get_all_data()
        else:
            return None
    

    def extract_exp_info(self):
        if 'experience' in self.user_headings:
            exp_block = self.heading_blocks[self.user_headings['experience']]
            exp = ExperienceParser(exp_block)
            return exp.get_all_data()
        else:
            return None
    

    def extract_training_info(self):
        if 'trainings' in self.user_headings:
            trang_block = self.heading_blocks[self.user_headings['trainings']]
            trang = TrainingParser(trang_block)
            return trang.get_all_data()
        else:
            return None


    def extract_objective(self):
        if 'objective' in self.user_headings:
            return self.heading_blocks[self.user_headings['objective']]
        else:
            return None
    

    def extract_skills(self):
        if 'skills' in self.user_headings:
            df = pd.read_csv(settings.BASE_DIR+'/engine/core/corpus/skills_IT.csv', header=None)
            df = df[0].apply(lambda x: x.lower())
            skills = df.tolist()

            skills_block =  self.heading_blocks[self.user_headings['skills']].replace('\n', '').replace('.','')
            skills_sub = []
            
            for skl in skills:
                search = re.search(skl, skills_block.lower())
                if search is not None:
                    skills_sub.append(search.group(0))

            return skills_sub
            
        else:
            return None