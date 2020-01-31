from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import jsonify, url_for, request
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


@api.route('/login/', methods=['POST'])
def login():
    auth = request.authorization
    try:
        username = auth.get('username')
        password = auth.get('password')
    except:
        return jsonify({'message': 'Couldn\'t verify user!'})
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User doesn\'t exists!',
                        'code': 404})
    if check_password_hash(user.password, password):
        token = jwt.encode({'id': user.id,
                            'exp': datetime.utcnow() + timedelta(minutes=15)},
                           Config.SECRET_KEY)
        return jsonify({'token': token.decode('UTF-8')})
    return jsonify({'message': 'Couldn\'t verify password!'})


@api.route('/', methods=['GET'])
@token_required
def index(current_user):
    json = jsonify({'users': url_for('.get_all_users', _external=True),
                    'wallets': url_for('.get_all_wallets', _external=True),
                    'parent_categories': url_for('.get_all_parent_categories', _external=True),
                    'categories': url_for('.get_all_categories', _external=True),
                    'transactions': url_for('.get_all_transactions', _external=True)})
    return json


# User
@api.route('/users/', methods=['GET'])
@token_required
def get_all_users(current_user):
    users = User.query.all()
    return jsonify({'users': [user.to_json() for user in users]})


@api.route('/users/<int:id>', methods=['GET'])
@token_required
def get_user(current_user, id):
    try:
        user = User.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The user doesn\'t exists.',
                        'code': 404})
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
    try:
        user = User.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The user doesn\'t exists.',
                        'code': 404})
    if current_user is user:
        data = request.json
        print('data: ', data)
        user.update(data)
        db.session.commit()
        return jsonify(user.to_json()), 200
    return jsonify({'message': 'You can\'t edit other users!',
                    'code': 403})


@api.route('/users/<int:id>', methods=['DELETE'])
@token_required
def delete_user(current_user, id):
    try:
        user = User.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The user doesn\'t exists.',
                        'code': 404})
    if current_user is user:
        user.delete()
        db.session.commit()
        return jsonify({'message': 'The user has been deleted.',
                        'code': 200})
    return jsonify({'message': 'You can\'t delete other users!',
                    'code': 403})


# Wallet
@api.route('/wallets/', methods=['GET'])
@token_required
def get_all_wallets(current_user):
    wallets = Wallet.query.all()
    return jsonify({'wallets': [wallet.to_json() for wallet in wallets]})


@api.route('/wallets/<int:id>', methods=['GET'])
@token_required
def get_wallet(current_user, id):
    try:
        wallet = Wallet.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The wallet doesn\'t exists.',
                        'code': 404})
    return jsonify(wallet.to_json()), 200


@api.route('/wallets/', methods=['POST'])
@token_required
def create_wallet(current_user):
    data = request.json
    data['owner_id'] = current_user.id
    wallet = Wallet.from_json(data)
    db.session.add(wallet)
    db.session.commit()
    return jsonify(wallet.to_json()), 201


@api.route('/wallets/<int:id>', methods=['PUT'])
def update_wallet(current_user, id):
    try:
        wallet = Wallet.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'Wallet doesn\'t exists.',
                       'code': 404})
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        data = request.json
        wallet.update(data)
        db.session.commit()
        return jsonify({wallet.to_json()}), 200
    return jsonify({'message': 'You can\'t edit the wallets of other users!',
                    'code': 403})


@api.route('/wallets/<int:id>', methods=["DELETE"])
@token_required
def delete_wallet(current_user, id):
    try:
        wallet = Wallet.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The wallet not found!',
                        'code': 404})
    wallet_owner = User.query.filter_by(id=wallet.owner_id)
    if current_user is wallet_owner:
        wallet.delete()
        db.session.commit()
        return jsonify({'message': 'The wallet has been deleted.',
                        'code': 200})
    return jsonify({'message': 'You can\'t delete the wallets of other users!',
                    'code': 403})


# ParentCategory
@api.route('/parent-categories/', methods=['GET'])
@token_required
def get_all_parent_categories(current_user):
    parent_categories = ParentCategory.query.all()
    return jsonify({'parent_categories': [parent_category.to_json()
                                          for parent_category in parent_categories],
                    'code': 200})


@api.route('/parent-categories/<int:id>', methods=['GET'])
@token_required
def get_parent_category(current_user, id):
    try:
        parent_category = ParentCategory.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The parent category doesn\'t exists.',
                        'code': 404})
    return jsonify(parent_category.to_json()), 200


@api.route('/parent-categories/', methods=['POST'])
@token_required
def create_parent_category(current_user):
    data = request.json
    try:
        wallet = Wallet.query.filter_by(id=data['wallet_id']).first()
    except:
        return jsonify({'message': 'The wallet doesn\'t exists!',
                        'code': 404})
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        new_parent_category = ParentCategory.from_json(data)
        db.session.add(new_parent_category)
        db.session.commit()
        return jsonify(new_parent_category.to_json()), 201
    return jsonify({'message': 'You can\'t add the parent categories to the wallet of other users!',
                    'code': 403})


@api.route('/parent-categories/<int:id>', methods=['PUT'])
@token_required
def update_parent_category(current_user, id):
    try:
        parent_category = ParentCategory.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The parent category doesn\'t exists.',
                        'code': 404})
    wallet = Wallet.query.filter_by(id=parent_category.wallet_id).first()
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        data = request.json
        parent_category.update(data)
        db.session.commit()
        return jsonify(parent_category.to_json()), 200
    return jsonify({'message': 'You can\'t edit the parent categories of other users!',
                    'code': 403})


@api.route('/parent-categories/<int:id>', methods=['DELETE'])
@token_required
def delete_parent_category(current_user, id):
    try:
        parent_category = ParentCategory.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The parent category doesn\'t exists!',
                        'code': 404})
    wallet = Wallet.query.filter_by(id=parent_category.wallet_id).first()
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        db.session.delete(parent_category)
        db.session.commit()
        return jsonify({'message': 'The parent category has been deleted.',
                        'code': 200})
    return jsonify({'message': 'You can\'t delete the parent categories of other users!',
                    'code': 403})


# Category
@api.route('/categories/', methods=['GET'])
@token_required
def get_all_categories(current_user):
    categories = Category.query.all()
    return jsonify({'categories': [category.to_json() for category in categories]})


@api.route('/categories/<int:id>', methods=['GET'])
@token_required
def get_category(current_user, id):
    try:
        category = Category.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The category doesn\'t exists.',
                        'code': 404})
    return jsonify(category.to_json()), 200


@api.route('/categories/', methods=['POST'])
@token_required
def create_category(current_user):
    data = request.json
    try:
        parent_category = ParentCategory.query.filter_by(id=data['parent_category_id']).first()
    except:
        return jsonify({'message': 'The parent category doesn\'t exists!',
                        'code': 404})
    wallet = Wallet.query.filter_by(id=parent_category.wallet_id).first()
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        new_category = Category.from_json(data)
        db.session.add(new_category)
        db.session.commit()
        return jsonify(new_category.to_json()), 201
    return jsonify({'message': 'You can\'t add the categories to the wallet of other users!',
                    'code': 403})


@api.route('/categories/<int:id>', methods=['PUT'])
@token_required
def update_category(current_user, id):
    try:
        category = Category.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The category doesn\'t exists.',
                        'code': 404})
    parent_category = ParentCategory.query.filter_by(id=category.parent_category_id).first()
    wallet = Wallet.query.filter_by(id=parent_category.wallet_id).first()
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        data = request.json
        category.update(data)
        db.session.commit()
        return jsonify(category.to_json()), 200
    return jsonify({'message': 'You can\'t edit the categories of other users!',
                    'code': 403})


@api.route('/categories/<int:id>', methods=['DELETE'])
@token_required
def delete_category(current_user, id):
    try:
        category = Category.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The category doesn\'t exists!',
                        'code': 404})
    parent_category = ParentCategory.query.filter_by(id=category.parent_category_id).first()
    wallet = Wallet.query.filter_by(id=parent_category.wallet_id).first()
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        category.delete()
        db.session.commit()
        return jsonify({'message': 'The category has been deleted.',
                        'code': 200})
    return jsonify({'message': 'You can\'t delete the categories of other users!',
                    'code': 403})


# Transaction
@api.route('/transactions/', methods=['GET'])
@token_required
def get_all_transactions(current_user):
    transactions = Transaction.query.all()
    return jsonify({'transactions': [transaction.to_json() for transaction in transactions]})


@api.route('/transactions/<int:id>', methods=['GET'])
@token_required
def get_transaction(current_user, id):
    try:
        transaction = Transaction.query.get_or_404(id)
    except:
        return jsonify({'message': 'The transaction doesn\'t exists.',
                        'code': 404})
    return jsonify(transaction.to_json()), 200


@api.route('/transactions/', methods=['POST'])
@token_required
def create_transaction(current_user):
    data = request.json
    try:
        category = Category.query.filter_by(id=data['category_id']).first()
    except:
        return jsonify({'message': 'The category doesn\'t exists!',
                        'code': 404})
    parent_category = ParentCategory.query.filter_by(id=category.parent_category_id).first()
    wallet = Wallet.query.filter_by(id=parent_category.wallet_id).first()
    wallet_owner = User.query.filter_by(id=wallet.owner_id).first()
    if current_user is wallet_owner:
        data['maker_id'] = current_user.id
        new_transaction = Transaction.from_json(data)
        db.session.add(new_transaction)
        db.session.commit()
        return jsonify(new_transaction.to_json()), 201
    return jsonify({'message': 'You can\'t add the transactions to the wallet of other users!',
                    'code': 403})


@api.route('/transactions/<int:id>', methods=['PUT'])
@token_required
def update_transaction(current_user, id):
    try:
        transaction = Transaction.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The transaction doesn\'t exists.',
                        'code': 404})
    maker = User.query.filter_by(id=transaction.maker_id).first()
    if current_user is maker:
        data = request.json
        transaction.update(data)
        db.session.commit()
        return jsonify(transaction.to_json()), 200
    return jsonify({'message': 'You can\'t edit the transactions of other users!',
                    'code': 403})


@api.route('/transactions/<int:id>', methods=['DELETE'])
@token_required
def delete_transaction(current_user, id):
    try:
        transaction = Transaction.query.filter_by(id=id).first()
    except:
        return jsonify({'message': 'The transaction doesn\'t exists!',
                        'code': 404})
    maker = User.query.filter_by(id=transaction.maker_id).first()
    if current_user is maker:
        transaction.delete()
        db.session.commit()
        return jsonify({'message': 'The transaction has been deleted.',
                        'code': 200})
    return jsonify({'message': 'You can\'t delete the transactions of other users!',
                    'code': 403})
