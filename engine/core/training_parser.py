import re
import pandas as pd


from django.conf import settings




class TrainingParser():


    def __init__(self, text):
        self.text = text
        self.trainings = []
        self.all_trainings = self.load_all_trainings()


    def load_all_trainings(self):
        df = pd.read_csv(settings.BASE_DIR+"/engine/core/corpus/trainings.csv", header=None)
        df[0] = df[0].apply(lambda x: x.lower())
        return df[0].tolist()


    def extract_user_trainings(self):
        for trang in self.all_trainings:
            if trang in self.text.lower():
                self.trainings.append(trang.title())


    def get_all_data(self):
        self.extract_user_trainings()
        return self.trainings