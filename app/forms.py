from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField, SelectField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class ReportForm(FlaskForm):
    reason = TextAreaField('신고 사유', validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('신고하기') 