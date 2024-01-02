import re
import pandas as pd
from django.conf import settings

global required_sub_headings

required_sub_headings = ['name', 'address', 'emails', 'phones']

class PersonalParser():

    def __init__(self, text):
        self.text = text
        self.filter_first_line()
        self.text = self.text.replace('\n',' ')


    def filter_first_line(self):
        titles = ['cv', 'ciriculum vitae', 'resume']
        unwanted_title = False
        for title in titles:
            if title in self.text.split("\n")[0].lower():
                unwanted_title = True
                break
        
        if unwanted_title:
            self.text = self.text.replace(self.text.split("\n")[0], '', 1)


    def extract_address(self):
        df = pd.read_csv(settings.BASE_DIR+"/engine/core/corpus/address_dz.csv", header=None)
        addr_dz = df[0].apply(lambda x: x.lower()).tolist()
        # create ngrams here instead of 1 gram
        for word in self.text.split(' '):
            if word.lower() in addr_dz:
                self.text = self.text.replace(word, " ", 1)
                return word.title()
                break
        else:
            return None
            
        
    def extract_name(self):
        # check for all capitals first
        search = re.search(r'([A-Z]+(\s[A-Z]+)+\s)|([A-Z]+[a-z]*(\s[A-Z]+[a-z]*)+)', self.text)
        if search is not None:
            return search.group(0)
        else:
            return None

        
    def extract_emails(self):
        emails = []
        found_iter = re.finditer(r'[a-zA-Z]+\d*(\.|_)?[a-zA-Z]+\d*@[a-zA-Z]+\.[a-zA-Z]+', self.text)
        for found in found_iter:
            emails.append(found.group(0))

        if len(emails) == 0: return None
        return emails


    def extract_phones(self):
        phones = []
        found_iter = re.finditer(r'(\(\+?\d{2,4}\)\s)?(\d{5,11}|\d{2,3}-\d{6,9})', self.text)
        for found in found_iter:
            phones.append(found.group(0))
        
        if len(phones) == 0: return None
        return phones


    def extract_websites(self):
        sites = []
        found_iter = re.finditer(r'http://([a-zA-Z]|\d)?([a-zA-Z]|\d)*\.([a-zA-Z]|\d)?([a-zA-Z]|\d)*.([a-zA-Z]|\d)?([a-zA-Z]|\d)*', self.text)
        for found in found_iter:
            sites.append(found.group(0))

        if len(sites) == 0: return None
        return sites


    def get_all_data(self):
        personal = {}
        personal['address'] = self.extract_address()
        personal['name'] = self.extract_name()
        personal['emails'] = self.extract_emails()
        personal['phones'] = self.extract_phones()
        personal['websites'] = self.extract_websites()
        return personal



class PersonalParserColon():
    global _sub_headings, sub_headings

    _sub_headings = {
                        'name':['full name', 'first name', 'last name', 'middle name / other names'],
                        'address':['physical street address for courier delivery (not a postal box)'],
                        'phones':['telephone home', 'telephone mobile', 'telephone office'],
                        'emails':['email 1', 'email 2'],
                        'marital status':['marital status'],
                        'date of birth':['date of birth', 'dob'],
                        'gender':['gender', 'sex'],
                        'country':['country of origin'],
                        'nationality':['nationality','present nationality'],
                        'languages':['languages and fluency level'],
                        'religion':['religion']
                    }

    sub_headings = {}

    @staticmethod
    def flat_subheadings():
        for key, values in _sub_headings.items():
            for v in values:
                sub_headings[v] = key
    

    def __init__(self, text):
        PersonalParserColon.flat_subheadings()
        self.text = text.replace('\n', ' ')
        self.user_headings = []         # headings in standard naming (name, address,..)

    

    def required_fields_not_found(self):
        not_found = []
        for req in required_sub_headings:
            if req not in self.user_headings:
                not_found.append(req)
        if len(not_found) == 0:
            return None
        else:
            return not_found          

    

    def get_all_data(self):
        found_sub_head = {}                     # found sub headings in text

        for sub_head in sub_headings:
            if sub_head+' ' in self.text.replace(":", " ").lower():
                self.user_headings.append(sub_headings[sub_head])
                found_sub_head[self.text.lower().find(sub_head)] = sub_head

        counter = 0
        sub_block = {}
        for sub_head_pos in sorted(found_sub_head):
            # get the start position of the information
            start = sub_head_pos + len(found_sub_head[sub_head_pos]+":")
            if counter == len(found_sub_head)-1:        # if reached last sub heading
                end = len(self.text)
            else:
                end = sorted(found_sub_head)[counter+1]
            value = self.text[start:end]                # split the string to obtain only sub heading info
            if sub_headings[found_sub_head[sub_head_pos]] in ['phones', 'emails']:
                if sub_headings[found_sub_head[sub_head_pos]] in sub_block:
                    sub_block[sub_headings[found_sub_head[sub_head_pos]]].append(value.strip())
                else:
                    sub_block[sub_headings[found_sub_head[sub_head_pos]]] = [value.strip()]
            else:
                if sub_headings[found_sub_head[sub_head_pos]] in sub_block:
                    sub_block[sub_headings[found_sub_head[sub_head_pos]]] += ' '+value.strip()
                else:
                    sub_block[sub_headings[found_sub_head[sub_head_pos]]] = value.strip()
            counter += 1

        not_found = self.required_fields_not_found()
        if not_found is not None:
            personal = PersonalParser(self.text)
            if 'address' in not_found:
                sub_block['address'] = personal.extract_address()
            if 'name' in not_found:
                sub_block['name'] = personal.extract_name()
            if 'emails' in not_found:
                sub_block['emails'] = personal.extract_emails()
            if 'phones' in not_found:
                sub_block['phones'] = personal.extract_phones()

        return sub_block
            
    