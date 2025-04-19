from app import create_app, db
from app.models import User, Product, Wallet, Transfer, Report, ProductImage, SearchLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'Wallet': Wallet,
        'Transfer': Transfer,
        'Report': Report,
        'ProductImage': ProductImage,
        'SearchLog': SearchLog
    }

if __name__ == '__main__':
    app.run(debug=True) 