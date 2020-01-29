from datetime import datetime

from flask import url_for
from werkzeug.security import generate_password_hash

from app import db


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    users = db.relationship('User', backref='role', lazy='dynamic')

    def _repr__(self):
        return self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    wallets = db.relationship('Wallet', backref='owner', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='maker', lazy='dynamic')

    @staticmethod
    def from_json(data):
        user = User()
        user.username = data.get('username')
        user.email = data.get('email')
        user.password = generate_password_hash(data.get('password'))
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        return user

    @staticmethod
    def generate_fake(count=10):
        import forgery_py
        from random import seed
        from sqlalchemy.exc import IntegrityError

        seed()
        for i in range(count):
            user = User()
            user.username = forgery_py.internet.user_name(True)
            user.email = forgery_py.internet.email_address()
            user.password = forgery_py.lorem_ipsum.word()
            user.confirmed = True
            user.first_name = forgery_py.name.first_name()
            user.last_name = forgery_py.name.last_name()
            user.date_joined = forgery_py.date.date(True)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        json = {
            'url': url_for('api.get_user', id=self.id, _external=True),
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirmed': self.confirmed,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_joined': self.date_joined,
            # 'role': self.role.id,
            'wallets': [url_for('api.get_wallet', id=wallet.id, _external=True)
                        for wallet in self.wallets],
            'transactions': [url_for('api.get_transaction', id=transaction.id, _external=True)
                             for transaction in self.transactions],
        }
        return json

    def update(self, data):
        user = User()
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.password = generate_password_hash(data.get('password')) or user.password
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        return user

    def delete(self):
        wallets = Wallet.query.filter_by(owner_id=self.id).all()
        for w in wallets:
            w.delete()
        db.session.delete(self)

    def __repr__(self):
        return self.username


class Wallet(db.Model):
    __tablename__ = 'wallets'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    currency = db.Column(db.String(64))
    initial_balance = db.Column(db.Float(precision=10), default=0.00)

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_categories = db.relationship('ParentCategory', backref='wallet', lazy='dynamic')

    @staticmethod
    def from_json(data):
        wallet = Wallet()
        wallet.title = data.get('title')
        wallet.created_at = datetime.utcnow()
        wallet.currency = data.get('currency')
        wallet.initial_balance = data.get('initial_balance')
        wallet.owner_id = data.get('owner_id')
        return wallet

    @staticmethod
    def generate_fake(count=5):
        import forgery_py
        from random import seed, randint

        seed()
        user_count = User.query.count()
        for i in range(count):
            user = User.query.offset(randint(0, user_count-1)).first()
            wallet = Wallet()
            wallet.title = forgery_py.name.title()
            wallet.created_at = forgery_py.date.date(True)
            wallet.currency = forgery_py.currency.code()
            wallet.initial_balance = randint(0, 1000)
            wallet.owner_id = user.id
            db.session.add(wallet)
            db.session.commit()

    def to_json(self):
        json = {
            'url': url_for('api.get_wallet', id=self.id, _external=True),
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at,
            'currency': self.currency,
            'initial_balance': self.initial_balance,
            # 'owner': url_for('api.get_user', id=self.owner_id, _external=True),
            'parent_categories': [url_for('api.get_parent_category', id=parent_category.id, _external=True)
                                  for parent_category in self.parent_categories],
        }
        return json

    def update(self, data):
        self.title = data.get('title', self.title)
        self.currency = data.get('currency', self.currency)
        self.initial_balance = data.get('initial_balance', self.initial_balance)
        return self

    def delete(self):
        parent_categories = ParentCategory.query.filter_by(wallet_id=self.id).all()
        for pc in parent_categories:
            pc.delete()
        db.session.delete(self)

    def __repr__(self):
        return self.title


class ParentCategory(db.Model):
    __tablename__ = 'parent_categories'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    budget = db.Column(db.Float(precision=10), default=0.00)
    is_income = db.Column(db.Boolean, default=False)

    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'))
    categories = db.relationship('Category', backref='parent_category', lazy='dynamic')

    @staticmethod
    def from_json(data):
        parent_category = ParentCategory()
        parent_category.title = data.get('title')
        parent_category.budget = data.get('budget')
        parent_category.is_income = data.get('is_income')
        parent_category.wallet_id = data.get('wallet_id')
        return parent_category

    @staticmethod
    def generate_fake(count=10):
        import forgery_py
        from random import seed, randint, choice

        seed()
        wallet_count = Wallet.query.count()
        for i in range(count):
            wallet = Wallet.query.offset(randint(0, wallet_count-1)).first()
            pc = ParentCategory()
            pc.title = forgery_py.name.title()
            pc.budget = randint(0, 1000)
            pc.is_income = choice([True, False])
            pc.wallet_id = wallet.id
            db.session.add(pc)
            db.session.commit()

    def to_json(self):
        json = {
            'url': url_for('api.get_parent_category', id=self.id, _external=True),
            'id': self.id,
            'title': self.title,
            'budget': self.budget,
            'is_income': self.is_income,
            'wallet': url_for('api.get_wallet', id=self.wallet.id, _external=True),
            'categories': [url_for('api.get_category', id=category.id, _external=True)
                           for category in self.categories],
        }
        return json

    def update(self, data):
        self.title = data.get('title', self.title)
        self.budget = data.get('budget', self.budget)
        self.is_income = data.get('is_income', self.is_income)
        return self

    def delete(self):
        categories = Category.query.filter_by(parent_category_id=self.id).all()
        for c in categories:
            c.delete()
        db.session.delete(self)

    def __repr__(self):
        return self.title


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    budget = db.Column(db.Float(precision=10), default=0.00)
    has_bills = db.Column(db.Boolean, default=False)

    parent_category_id = db.Column(db.ForeignKey('parent_categories.id'))
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')

    @staticmethod
    def from_json(data):
        category = Category()
        category.title = data.get('title')
        category.budget = data.get('budget')
        category.has_bills = data.get('has_bills')
        category.parent_category_id = data.get('parent_category_id')
        return category

    @staticmethod
    def generate_fake(count=15):
        import forgery_py
        from random import seed, randint, choice

        seed()
        parent_category_count = ParentCategory.query.count()
        for i in range(count):
            parent_category = ParentCategory.query.offset(randint(0, parent_category_count-1)).first()
            c = Category()
            c.title = forgery_py.name.title()
            c.budget = randint(0, 1000)
            c.has_bills = choice([True, False])
            c.parent_category_id = parent_category.id
            db.session.add(c)
            db.session.commit()

    def to_json(self):
        json = {
            'url': url_for('api.get_category', id=self.id, _external=True),
            'id': self.id,
            'title': self.title,
            'budget': self.budget,
            'has_bills': self.has_bills,
            'parent_category': url_for('api.get_parent_category', id=self.parent_category_id, _external=True),
            'transactions': [url_for('api.get_transaction', id=transaction.id, _external=True)
                             for transaction in self.transactions],
        }
        return json

    def update(self, data):
        self.title = data.get('title', self.title)
        self.budget = data.get('budget', self.budget)
        self.has_bills = data.get('has_bills', self.has_bills)
        self.parent_category_id = data.get('parent_category_id', self.parent_category_id)
        return self

    def delete(self):
        transactions = Transaction.query.filter_by(category_id=self.id).all()
        for t in transactions:
            t.delete()
        db.session.delete(self)

    def __repr__(self):
        return self.title


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float(precision=10), default=0.00)
    description = db.Column(db.Text())
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    category_id = db.Column(db.ForeignKey('categories.id'))
    maker_id = db.Column(db.ForeignKey('users.id'))

    @staticmethod
    def from_json(data):
        transaction = Transaction()
        transaction.amount = data.get('amount')
        transaction.description = data.get('description')
        transaction.category_id = data.get('category_id')
        transaction.maker_id = data.get('maker_id')
        return transaction

    @staticmethod
    def generate_fake(count=30):
        import forgery_py
        from random import seed, randint, choice

        seed()
        category_count = Category.query.count()
        for i in range(count):
            category = Category.query.offset(randint(0, category_count-1)).first()
            parent_category = ParentCategory.query.filter_by(id=category.parent_category_id).first()
            wallet = Wallet.query.filter_by(id=parent_category.wallet_id).first()
            maker = User.query.filter_by(id=wallet.owner_id).first()
            t = Transaction()
            t.amount = randint(0, 10000)
            t.description = forgery_py.lorem_ipsum.sentences(randint(1, 3))
            t.created_at = forgery_py.date.date(True)
            t.category_id = category.id
            t.maker_id = maker.id
            db.session.add(t)
            db.session.commit()

    def to_json(self):
        json = {
            'url': url_for('api.get_transaction', id=self.id, _external=True),
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'created_at': self.created_at,
            'category': url_for('api.get_category', id=self.category_id, _external=True),
            'maker': url_for('api.get_user', id=self.maker_id, _external=True),
        }
        return json

    def update(self, data):
        self.amount = data.get('amount', self.amount)
        self.description = data.get('description', self.description)
        self.category_id = data.get('category_id', self.category_id)
        return self

    def delete(self):
        db.session.delete(self)

    def __repr__(self):
        return '{} {}'.format(self.amount, self.category)
