import click
from flask.cli import with_appcontext
from app import db
from app.models import Report

@click.command('create-tables')
@with_appcontext
def create_tables():
    """데이터베이스 테이블 생성"""
    db.create_all()
    click.echo('데이터베이스 테이블이 생성되었습니다!')

def init_app(app):
    app.cli.add_command(create_tables) 