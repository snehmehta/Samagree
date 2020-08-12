
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from flask_pymongo import pymongo

from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordForm, ResetPasswordRequestForm
from app import app, mongo, db
from app.models import User
from app.email import send_password_reset_email

from werkzeug.urls import url_parse
from datetime import datetime
from bson.objectid import ObjectId
from hashlib import md5

# helpers 

def convert_user(u):
    user = User(username=u['username'], email=u['email'])
    user.set_details(last_seen=u['last_seen'], about_me=u['about_me'], uid=u['_id'])
    return user

# routes

@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])  
@login_required
def index():

    form = PostForm()
    if form.validate_on_submit():

        db.post.insert_one({
            'user_id' : current_user.id,
            'username' : current_user.username,
            'timestamp': datetime.utcnow().timestamp(),
            'body' : form.post.data
        })

        flash('Your post is live now!')
        return redirect(url_for('index'))

    offset = request.args.get('offset', 0, type=int)
    limit = app.config['POST_PER_PAGE']

    starting_id = db.post.find().sort('_id', pymongo.DESCENDING)
    last_id = starting_id[offset]['_id']

    leng = starting_id.count()

    if not offset + limit >= leng:
        next_url = '/index?offset=' + str(offset + limit)
    else:
        next_url = '/index?offset=' + str(leng - limit)

    if not offset - limit < 0:
        prev_url = '/index?offset=' + str(offset - limit)
    else:
        prev_url = '/index?offset=' + str(0)

    posts = current_user.followed_posts(last_id, limit)
    _posts = []

    for post in posts:

        art = {}
        art['author'] = {'username' : post['posts']['username']}
        art['body'] = post['posts']['body']
        _posts.append(art)    

    return render_template("index.html", title="Home", posts=_posts, form=form, next_url=next_url, prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():

    offset = request.args.get('offset', 0, type=int)
    limit = app.config['POST_PER_PAGE']

    starting_id = db.post.find().sort('_id', pymongo.DESCENDING)
    last_id = starting_id[offset]['_id']
    leng = starting_id.count()

    
    if not offset + limit >= leng:
        next_url = '/explore?offset=' + str(offset + limit)
    else:
        next_url = '/explore?offset=' + str(leng - limit)

    if not offset - limit < 0:
        prev_url = '/explore?offset=' + str(offset - limit)
    else:
        prev_url = '/explore?offset=' + str(0)
    
    posts = db.post.aggregate([
        {'$sort' : {'_id' : -1}},
        {'$match' : {'_id' : {'$lte' : last_id}}},
        {'$limit' : limit}
    ])

    _posts = []

    for post in posts:
    
        art = {}
        art['author'] = {'username' : post['username']}
        art['body'] = post['body']
        art['timestamp'] = post['timestamp']
        _posts.append(art)
    
    return render_template('index.html', title='Explore', posts=_posts,next_url=next_url, prev_url=prev_url)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():

        user = db.user.find_one({'username' : form.username.data})

        if user is None or not User.check_password(user['password_hash'],form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        user_obj = User(user['username'], user['email'])
        login_user(user_obj, remember=form.remember_me.data)
        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['POST', 'GET'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        u = db.user.insert_one({
            'username' : user.username,
            'email' : user.email,
            'password_hash' : user.password,
            'about_me' : 'Samagree User'
        })
        public_id = ObjectId('5ed312f8fcab84670a9091b6')
        db.following.insert_one({
            'user_id' : u.inserted_id,
            'followingId' : [public_id]
        })

        flash('Congratulation, you are now a registered user!')

        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):

    form = EmptyForm()

    u = db.user.find_one({'username' : username})

    if u is not None:
        user = convert_user(u)

        # TODO: Pagination in user and add link in user.html
        # _posts = db.post.find({'user_id' : u['_id']}).sort('_id' : -1).limit(limit)

        posts = [
            {'author' : user, 'body' : 'Test post 1'},
            {'author' : user, 'body' : 'Test post 2'},
        ]

        return render_template('user.html', user=user, posts=posts, form=form)
    return redirect(url_for('user',username=current_user.username))

@app.before_request
def before_request():
    if current_user.is_authenticated:
        date = datetime.utcnow()
        user = db.user.find_one_and_update({'username' : current_user.username},{'$set' : {'last_seen' : date}})
        current_user.set_details(last_seen=date, about_me=user['about_me'], uid=user['_id'])

@app.route('/edit_profile', methods=['POST','GET'])
@login_required
def edit_profile():

    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        
        db.user.find_one_and_update(
            {'username' : current_user.username},
            {
                '$set' : 
                {
                    'username' : form.username.data,
                    'about_me' : form.about_me.data
                }
            }
        )
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data

        flash(' Your Changes have been Saved')

        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/follow/<username>', methods=['POST', 'GET'])
@login_required
def follow(username):
    
    form = EmptyForm()

    if form.validate_on_submit():

        u = db.user.find_one({'username': username})

        if u is None:
            flash(f'User {username} not found')

            return redirect(url_for('index'))

        user = convert_user(u)

        if user == current_user:
            flash('You cannot follow yourself')
            return redirect(url_for('user',username=username))
        
        current_user.follow(user)
        flash(f'You are following {username}!')

        return redirect(url_for('user',username=username))
    else:
        return redirect(url_for('index'))

@app.route('/unfollow/<username>', methods=['POST', 'GET'])
@login_required
def unfollow(username):

    form = EmptyForm()
    if form.validate_on_submit():
        u = db.user.find_one({'username': username})

        if u is None:
            flash('User {username} not found.')
            return redirect(url_for('index'))

        user = convert_user(u)

        if user == current_user:
            flash(f'You cannot unfollow yourself')
            return redirect(url_for('index'))

        current_user.unfollow(user)

        flash(f'You are not following {username}.')
        return redirect(url_for('user',username=username))
    else:
        return redirect(url_for('index'))


@app.route('/reset_password_request', methods=['POST', 'GET'])
def reset_password_request():

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ResetPasswordRequestForm()
    
    if form.validate_on_submit():

        u = db.user.find_one({'email' : form.email.data})
        if u :
            user = convert_user(u)
            send_password_reset_email(user)
        
        flash('Check your email for instructions to reset your password')

        return redirect(url_for('login'))

    return render_template('reset_password_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_password(token):

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)

        db.user.find_one_and_update({'_id' : user.id}, {'$set' :{
            'password_hash' : user.password
        }})

        flash('Your password has been reset successfully !')

        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)

