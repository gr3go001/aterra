from dotenv import load_dotenv
import os 


env_file = ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env"
load_dotenv(env_file)

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
