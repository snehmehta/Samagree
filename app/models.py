from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login, db
from hashlib import md5
from flask_pymongo import pymongo
from time import time 
from app import app 
import jwt 

class User():

    def __init__(self, username, email):

        self.username = username
        self.email = email

    @staticmethod
    def is_authenticated():
        return True 

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def set_details(self, last_seen, about_me, uid):
        self.last_seen = last_seen
        self.about_me = about_me
        self.id = uid
        
    @staticmethod
    def check_password(password_hash, password):
        return check_password_hash(password_hash, password)


    @login.user_loader
    def load_user(username):
        u = db.user.find_one({'username' : username})
        if not u:
             return None
        
        return User(username=u['username'],email=u['email'])

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()

        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):

        if not self.is_following(user):
            db.following.find_one_and_update(
                {'user_id': self.id},
                {'$push' : {'followingId' : user.id}}
            )
    
    def unfollow(self, user):
        
        if self.is_following(user):
            db.following.find_one_and_update(
                {'user_id' : self.id},
                {'$pull': {'followingId': user.id}}
            )
    
    def is_following(self,user):
        
        count = db.following.find({
            'user_id' : self.id,
            'followingId' : 
                {
                    '$in' : [user.id]
                }
            }).count()
        
        return count > 0

    def followed_posts(self, last_id, limit):

        t = db.following.aggregate([
            {'$match': {'user_id': self.id}},
            {'$unwind': '$followingId'},
            {'$lookup': {
                'from' : 'post',
                'localField' : 'followingId',
                'foreignField' : 'user_id',
                'as' : 'posts'
            }},
            {'$project' : {'posts' : 1, '_id' : 0}},
            {'$unwind': '$posts' },
            {'$sort' : {'posts._id' : pymongo.DESCENDING}},
            {'$match' : {'posts._id' : {'$lte': last_id}}},
            {'$limit' : limit},
        ])

        return list(t)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password' : str(self.id), 'exp' : time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        ).decode('utf-8')
    
    @staticmethod
    def verify_reset_password_token(token):
        try: 
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithm=['HS256'])['reset_password']
        except:
            return 
        u = db.user.find_one({'user_id' : id})
        return helper.user(u)
    

