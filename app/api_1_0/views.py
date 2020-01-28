from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import jsonify, url_for, request, g, make_response
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from . import api
from .. import db

from ..models import User, Wallet, ParentCategory, Category, Transaction


def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('x-access-token', None)

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, Config.SECRET_KEY)
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return func(current_user, *args, **kwargs)

    return wrapper


@api.route('/login', methods=['GET'])
def login():
    auth = request.authorization
    try:
        username = auth.get('username')
        password = auth.get('password')
    except:
        return jsonify({'message': 'Couldn\'t verify user!'})

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User doesn\'t exists!'})

    if check_password_hash(user.password, password):
        token = jwt.encode({'id': user.id,
                            'exp': datetime.utcnow() + timedelta(minutes=15)},
                           Config.SECRET_KEY)
        return jsonify({'token': token.decode('UTF-8')})
    return jsonify({'message': 'Couldn\'t verify password!'})


@api.route('/')
@token_required
def index(current_user):
    json = jsonify({'users': url_for('.get_users', _external=True),
                    'wallets': url_for('.get_wallets', _external=True),
                    'parent_categories': url_for('.get_parent_categories', _external=True),
                    'categories': url_for('.get_categories', _external=True),
                    'transactions': url_for('.get_transactions', _external=True)})
    return json


# User
@api.route('/users/')
@token_required
def get_users(current_user):
    users = User.query.all()
    return jsonify({'users': [user.to_json() for user in users]})


@api.route('/users/<int:id>')
@token_required
def get_user(current_user, id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


@api.route('/users/', methods=['POST'])
@token_required
def create_user(current_user):
    user = User.from_json(request.json)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_json()), 201


@api.route('/users/<int:id>', methods=['PUT'])
@token_required
def update_user(current_user, id):
    data = request.json
    try:
        user = User.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'User doesn\'t exists.'})
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.password = generate_password_hash(data.get('password')) or user.password
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    db.session.commit()
    return jsonify(user.to_json())


@api.route('/users/<int:id>', methods=['DELETE'])
@token_required
def delete_user(current_user, id):
    try:
        user = User.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'User doesn\'t exists.'})
    if current_user is user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User has been deleted.'})
    return jsonify({'message': 'You can\'t delete other users!'})


# Wallet
@api.route('/wallets/')
@token_required
def get_wallets(current_user):
    wallets = Wallet.query.all()
    return jsonify({'wallets': [wallet.to_json() for wallet in wallets]})


@api.route('/wallets/<int:id>')
@token_required
def get_wallet(current_user, id):
    wallet = Wallet.query.get_or_404(id)
    return jsonify(wallet.to_json())


@api.route('/wallets/', methods=['POST'])
@token_required
def create_wallet(current_user):
    request.json['owner_id'] = current_user
    wallet = Wallet.from_json(request.json)
    wallet.owner_id = current_user.id
    db.session.add(wallet)
    db.session.commit()
    return jsonify(wallet.to_json()), 201


@api.route('/wallets/<int:id>', methods=["DELETE"])
@token_required
def delete_wallet(current_user, id):
    try:
        wallet = Wallet.query.filter_by(id=id, owner=current_user).first()
    except:
        return jsonify({'message': 'Wallet not found!'})
    db.session.delete(wallet)
    db.session.commit()
    return jsonify({'message': 'Wallet has been deleted.'})


# ParentCategory
@api.route('/parent-categories/')
@token_required
def get_parent_categories(current_user):
    parent_categories = ParentCategory.query.all()
    return jsonify({'parent_categories': [parent_category.to_json()
                                          for parent_category in parent_categories]})


@api.route('/parent-categories/<int:id>')
@token_required
def get_parent_category(current_user, id):
    parent_category = ParentCategory.query.get_or_404(id)
    return jsonify(parent_category.to_json())


# Category
@api.route('/categories/')
@token_required
def get_categories(current_user):
    categories = Category.query.all()
    return jsonify({'categories': [category.to_json() for category in categories]})


@api.route('/categories/<int:id>')
@token_required
def get_category(current_user, id):
    category = Category.query.get_or_404(id)
    return jsonify(category.to_json())


# Transaction
@api.route('/transactions/')
@token_required
def get_transactions(current_user):
    transactions = Transaction.query.all()
    return jsonify({'transactions': [transaction.to_json() for transaction in transactions]})


@api.route('/transactions/<int:id>')
@token_required
def get_transaction(current_user, id):
    transaction = Transaction.query.get_or_404(id)
    return jsonify(transaction.to_json())
