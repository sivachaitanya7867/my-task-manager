from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FileField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_wtf.file import FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    bio = TextAreaField('Bio', validators=[Length(max=200)])
    submit = SubmitField('Update')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png'])])
    video = FileField('Video', validators=[FileAllowed(['mp4', 'avi'])])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')

class FollowRequestForm(FlaskForm):
    receiver_id = IntegerField('Receiver ID', validators=[DataRequired()])
    submit = SubmitField('Send Follow Request')

class AcceptFollowRequestForm(FlaskForm):
    request_id = IntegerField('Request ID', validators=[DataRequired()])
    submit = SubmitField('Accept Follow Request')

class DeclineFollowRequestForm(FlaskForm):
    request_id = IntegerField('Request ID', validators=[DataRequired()])
    submit = SubmitField('Decline Follow Request')

class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Create/Update Group')

class JoinGroupForm(FlaskForm):
    submit = SubmitField('Join Group')


