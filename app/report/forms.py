from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length

class ReportForm(FlaskForm):
    reason_type = RadioField('신고 유형', choices=[
        ('scam', '사기/기만'),
        ('fake', '가품/위조품'),
        ('inappropriate', '부적절한 내용'),
        ('harassment', '사용자 괴롭힘'),
        ('other', '기타')
    ], validators=[DataRequired()])
    
    reason = TextAreaField('상세 사유', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('신고하기') 