import os 

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://joao:impossivel999@localhost/agenda'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)