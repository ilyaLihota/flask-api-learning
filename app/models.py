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
            'transactions': [transaction.id for transaction in self.transactions],
        }
        return json

    @staticmethod
    def from_json(json):
        user = User()
        user.username = json.get('username')
        user.email = json.get('email')
        user.password = generate_password_hash(json.get('password'))
        user.first_name = json.get('first_name')
        user.last_name = json.get('last_name')
        return user

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

    def to_json(self):
        json = {
            'url': url_for('api.get_wallet', id=self.id, _external=True),
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at,
            'currency': self.currency,
            'initial_balance': self.initial_balance,
            'owner': url_for('api.get_user', id=self.owner_id, _external=True),
            'parent_categories': [url_for('api.get_parent_category', id=parent_category.id, _external=True)
                                  for parent_category in self.parent_categories],
        }
        return json

    @staticmethod
    def from_json(json):
        wallet = Wallet()
        wallet.title = json.get('title')
        wallet.created_at = datetime.utcnow()
        wallet.currency = json.get('currency')
        wallet.initial_balance = json.get('initial_balance')
        wallet.owner_id = json.get('owner_id')
        return wallet

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

    def to_json(self):
        json = {
            'url': url_for('api.get_parent_category', id=self.id, _external=True),
            'id': self.id,
            'title': self.title,
            'budget': self.budget,
            'is_income': self.is_income,
            'wallet': url_for('api.get_wallet', id=self.wallet.id, _external=True),
            'categories': [url_for('api.get_category', id=category.id)
                           for category in self.categories],
        }
        return json

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

    def __repr__(self):
        return '{} {}'.format(self.amount, self.category)
