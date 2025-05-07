import os 

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://aterra_user:c3zgMh4oL9Wn4Hn4RQe0ThierNPEGyEH@dpg-d0dna515pdvs739cjjqg-a/aterradb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'uma-string-supersecreta-padrao')