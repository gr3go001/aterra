import os
from dotenv import load_dotenv
from app import create_app, db


load_dotenv=(".env.production")
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
