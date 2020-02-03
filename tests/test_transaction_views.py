import json
import unittest
from base64 import b64encode
from random import randint, choice

from flask import url_for

from app import create_app, db
from app.models import User, Wallet, ParentCategory, Category, Transaction


class CategoryTestCase(unittest.TestCase):

    @staticmethod
    def get_api_headers(username: str, password: str) -> dict:
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    @staticmethod
    def get_token_headers(token: str) -> dict:
        return {'x-access-token': token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'}

    def setUp(self) -> None:
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create user
        self.user = User.from_json(
            {'username': 'test_user',
             'email': 'test_user@example.com',
             'password': 'new_password',
             'confirmed': True,
             'first_name': 'test_first_name',
             'last_name': 'test_last_name'}
        )
        db.session.add(self.user)

        # Login user
        response = self.client.post(
            url_for('api.login'),
            headers=self.get_api_headers('test_user', 'new_password')
        )
        self.token = response.json['token']

        # Create wallet
        self.wallet = Wallet.from_json({'title': 'test_wallet',
                                        'currency': 'usd',
                                        'initial_balance': randint(0, 100),
                                        'owner_id': self.user.id})
        db.session.add(self.wallet)
        db.session.commit()

        # Create parent category
        self.parent_category = ParentCategory.from_json({'title': 'test_parent_category',
                                                         'budget': randint(0, 1000),
                                                         'is_income': choice([True, False]),
                                                         'wallet_id': self.wallet.id})
        db.session.add(self.parent_category)
        db.session.commit()

        # Create category
        self.category = Category.from_json({'title': 'test_category',
                                            'budget': randint(0, 1000),
                                            'has_bills': choice([True, False]),
                                            'parent_category_id': self.parent_category.id})
        db.session.add(self.category)
        db.session.commit()

        # Create transaction
        self.transaction = Transaction.from_json({'amount': randint(1, 2000),
                                                  'description': 'some description',
                                                  'category_id': self.category.id,
                                                  'maker_id': self.user.id})
        db.session.add(self.transaction)
        db.session.commit()

        self.data = {'amount': randint(1, 2000),
                     'description': 'some description 2',
                     'category_id': self.category.id,
                     'maker_id': self.user.id}

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_all_transactions(self):
        """
        The test case for get_all_transactions view.
        """
        for i in range(3):
            t = Transaction.from_json({'amount': randint(1, 2000),
                                       'description': 'some description{}'.format(i),
                                       'category_id': self.category.id,
                                       'maker_id': self.user.id})
            db.session.add(t)
        db.session.commit()

        response = self.client.get(
            url_for('api.get_all_transactions'),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.json['transactions']), 4)

    def test_get_transaction(self):
        """
        The test case for get_transaction view.
        """
        response = self.client.get(
            url_for('api.get_transaction', id=self.transaction.id),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.json['amount'] == self.transaction.amount)
        self.assertTrue(response.json['description'] == self.transaction.description)
        self.assertTrue(response.json['category'] == url_for('api.get_category',
                                                             id=self.transaction.category_id,
                                                             _external=True))
        self.assertTrue(response.json['maker'] == url_for('api.get_user',
                                                             id=self.transaction.maker_id,
                                                             _external=True))

    def test_create_transaction(self):
        """
        The test case for create_transaction view.
        """
        response = self.client.post(
            url_for('api.create_transaction'),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )

        self.assertTrue(response.status_code == 201)
        self.assertTrue(response.json['amount'] == self.data['amount'])
        self.assertTrue(response.json['description'] == self.data['description'])
        self.assertTrue(response.json['category'] == url_for('api.get_category',
                                                             id=self.data['category_id'],
                                                             _external=True))
        self.assertTrue(response.json['maker'] == url_for('api.get_user',
                                                          id=self.data['maker_id'],
                                                          _external=True))

    def test_update_transaction(self):
        """
        The test case for update_transaction view.
        """
        response = self.client.put(
            url_for('api.update_transaction', id=self.transaction.id),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.json['amount'] == self.data['amount'])
        self.assertTrue(response.json['description'] == self.data['description'])
        self.assertTrue(response.json['category'] == url_for('api.get_category',
                                                             id=self.data['category_id'],
                                                             _external=True))
        self.assertTrue(response.json['maker'] == url_for('api.get_user',
                                                          id=self.data['maker_id'],
                                                          _external=True))

    def test_delete_transaction(self):
        """
        The test case for delete_transaction view.
        """
        response = self.client.delete(
            url_for('api.delete_transaction', id=self.transaction.id),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertIsNone(Transaction.query.first())
