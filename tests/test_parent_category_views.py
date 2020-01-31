import json
import unittest
from base64 import b64encode
from random import randint, choice

from flask import url_for

from app import create_app, db
from app.models import User, Wallet, ParentCategory


class ParentCategoryTestCase(unittest.TestCase):

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

        self.data = {'title': 'test_parent_category2',
                     'budget': randint(0, 1000),
                     'is_income': choice([True, False]),
                     'wallet_id': self.wallet.id}

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_all_parent_categories(self):
        """
        The test case for get_all_parent_categories view.
        """
        for i in range(3):
            p_c = ParentCategory.from_json({'title': 'test_parent_category{}'.format(i),
                                            'budget': randint(0, 1000),
                                            'is_income': choice([True, False]),
                                            'wallet_id': self.wallet.id})
            db.session.add(p_c)
        db.session.commit()

        response = self.client.get(
            url_for('api.get_all_parent_categories'),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.json['parent_categories']) == 4)

    def test_get_parent_category(self):
        """
        The test case for get_parent_category view.
        """
        response = self.client.get(
            url_for('api.get_parent_category', id=self.parent_category.id),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.json['title'] == self.parent_category.title)
        self.assertTrue(response.json['budget'] == self.parent_category.budget)
        self.assertTrue(response.json['is_income'] == self.parent_category.is_income)
        self.assertTrue(response.json['wallet'] == url_for('api.get_wallet',
                                                           id=self.parent_category.wallet_id,
                                                           _external=True))

    def test_create_parent_category(self):
        """
        The test case for create_parent_category view.
        """
        response = self.client.post(
            url_for('api.create_parent_category'),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )

        self.assertTrue(response.status_code == 201)
        self.assertTrue(response.json['title'] == self.data['title'])
        self.assertTrue(response.json['budget'] == self.data['budget'])
        self.assertTrue(response.json['is_income'] == self.data['is_income'])
        self.assertTrue(response.json['wallet'] == url_for('api.get_wallet',
                                                           id=self.data['wallet_id'],
                                                           _external=True))

    def test_update_parent_category(self):
        """
        The test case for update_parent_category view.
        """
        parent_category = ParentCategory.query.first()
        response = self.client.put(
            url_for('api.update_parent_category', id=parent_category.id),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.json['title'] == self.data['title'])
        self.assertTrue(response.json['budget'] == self.data['budget'])
        self.assertTrue(response.json['is_income'] == self.data['is_income'])
        self.assertTrue(response.json['wallet'] == url_for('api.get_wallet',
                                                           id=self.data['wallet_id'],
                                                           _external=True))

    def test_delete_parent_category(self):
        """
        The test case for delete_parent_category view.
        """
        response = self.client.delete(
            url_for('api.delete_parent_category', id=self.parent_category.id),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertIsNone(ParentCategory.query.first())
