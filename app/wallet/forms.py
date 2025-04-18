from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, NumberRange, Email, ValidationError
from app.models import User

class TransferForm(FlaskForm):
    amount = IntegerField('송금액', validators=[DataRequired(), NumberRange(min=1)])
    receiver_email = StringField('받는 사람 이메일', validators=[DataRequired(), Email()])
    submit = SubmitField('송금하기')

class ChargeForm(FlaskForm):
    """지갑 충전 폼"""
    amount = IntegerField('충전액', validators=[
        DataRequired(),
        NumberRange(min=1000, max=1000000, message='충전액은 1,000원에서 1,000,000원 사이여야 합니다.')
    ])
    payment_method = SelectField('결제 수단', choices=[
        ('card', '신용카드'),
        ('bank', '계좌이체'),
        ('virtual', '가상계좌'),
        ('phone', '휴대폰결제')
    ], validators=[DataRequired()])
    submit = SubmitField('충전하기') 