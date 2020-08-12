import os 

db_user = os.environ.get('db_user')
db_password = os.environ.get('db_pass')


class Config:
    # Flask secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hehehaha'

    # Mongo connection string
    MONGO_URI = f"mongodb+srv://{db_user}:{db_password}@cluster0-qbsa9.mongodb.net/test?retryWrites=true&w=majority"

    # mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['whatweare9@gmail.com']
    
    # pagination
    POST_PER_PAGE = 5