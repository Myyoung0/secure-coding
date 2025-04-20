from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    remember_me = BooleanField('로그인 상태 유지')
    submit = SubmitField('로그인')

class RegistrationForm(FlaskForm):
    username = StringField('사용자명', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('비밀번호 확인', validators=[DataRequired(), EqualTo('password')])
    bank_name = StringField('은행명', validators=[DataRequired(), Length(max=50)])
    account_number = StringField('계좌번호', validators=[DataRequired(), Length(max=30)])
    submit = SubmitField('회원가입')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('이미 등록된 이메일입니다. 다른 이메일을 사용해주세요.')

class EditProfileForm(FlaskForm):
    username = StringField('사용자명', validators=[DataRequired(), Length(min=2, max=64)])
    profile_image = FileField('프로필 이미지', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    submit = SubmitField('저장') 