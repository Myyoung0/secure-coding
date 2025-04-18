from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, IntegerField, SelectField, MultipleFileField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class ProductForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(min=2, max=120)])
    description = TextAreaField('설명', validators=[DataRequired(), Length(min=10, max=2000)])
    price = IntegerField('가격', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('카테고리', validators=[DataRequired()], choices=[
        ('electronics', '전자제품'),
        ('fashion', '패션/의류'),
        ('books', '도서'),
        ('sports', '스포츠/레저'),
        ('furniture', '가구/인테리어'),
        ('beauty', '뷰티/미용'),
        ('toys', '장난감/취미'),
        ('etc', '기타')
    ])
    location = StringField('지역', validators=[DataRequired(), Length(min=2, max=100)])
    images = MultipleFileField('이미지', validators=[
        FileRequired('최소 한 개의 이미지를 업로드해주세요.'),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '이미지 파일만 업로드 가능합니다.')
    ])
    submit = SubmitField('등록하기') 