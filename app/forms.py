from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,  BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User
from app import db 

class LoginForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        # from IPython.core.debugger import set_trace
        # set_trace()
        user = db.user.find_one({'username' : username.data})
        if user is not None:
            raise ValidationError('Please use a different username')

    def validate_email(self, email):
        user = db.user.find_one({'email' : email.data})
        if user is not None:
            raise ValidationError('Please use a different email address')

class EditProfileForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self,original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.user.find_one({'username': username.data})
            if user is not None:
                raise ValidationError('Please use a different username')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired(),Length(min=1,max=140)])
    submit = SubmitField('Submit')

class ResetPasswordRequestForm(FlaskForm):

    email = StringField('Email', validators=[DataRequired(),Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    
    password = StringField('Password', validators=[DataRequired()])
    password2 = StringField('Repeat Password', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Request Password Reset')
