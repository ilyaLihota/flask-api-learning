import json
import unittest
from base64 import b64encode
from random import randint, choice

from flask import url_for

from app import create_app, db
from app.models import User, Wallet


class WalletTestCase(unittest.TestCase):

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

        # Login new_user
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

        self.data = {'title': 'test_wallet2',
                     'currency': 'eur',
                     'initial_balance': randint(0, 100),
                     'owner_id': self.user.id}

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_all_wallets(self):
        """
        The test case for get_all_wallets view.
        """
        # Create 3 wallets
        for i in range(3):
            wallet = Wallet.from_json({'title': 'wallet{}'.format(i),
                                       'currency': choice(['usd', 'eur', 'rub']),
                                       'initial_balance': randint(0, 100),
                                       'owner_id': self.user.id})
            db.session.add(wallet)
        db.session.commit()

        response = self.client.get(
            url_for('api.get_all_wallets'),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.json['wallets']) == 4)

    def test_get_wallet(self):
        """
        The test case for get_wallet view.
        """
        response = self.client.get(
            url_for('api.get_wallet', id=self.wallet.id),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.json['title'] == self.wallet.title)
        self.assertTrue(response.json['currency'] == self.wallet.currency)
        self.assertTrue(response.json['initial_balance'] == self.wallet.initial_balance)
        self.assertTrue(response.json['owner'] == url_for('api.get_user',
                                                          id=self.wallet.owner_id,
                                                          _external=True))

    def test_create_wallet(self):
        """
        The test case for create_wallet view.
        """
        response = self.client.post(
            url_for('api.create_wallet'),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )

        self.assertTrue(response.status_code == 201)
        self.assertTrue(response.json['title'] == self.data['title'])
        self.assertTrue(response.json['currency'] == self.data['currency'])
        self.assertTrue(response.json['initial_balance'] == self.data['initial_balance'])
        self.assertTrue(response.json['owner'] == url_for('api.get_user',
                                                          id=self.user.id,
                                                          _external=True))

    def test_update_wallet(self):
        """
        The test case for update_wallet.
        """
        response = self.client.put(
            url_for('api.update_wallet', id=self.wallet.id),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )

        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.json['title'] == self.data['title'])
        self.assertTrue(response.json['currency'] == self.data['currency'])
        self.assertTrue(response.json['initial_balance'] == self.data['initial_balance'])
        self.assertTrue(response.json['owner'] == url_for('api.get_user',
                                                          id=self.user.id,
                                                          _external=True))

    def test_delete_wallet(self):
        """
        The test case for delete_wallet view.
        """
        response = self.client.delete(
            url_for('api.delete_wallet', id=self.wallet.id),
            headers=self.get_token_headers(self.token)
        )

        self.assertTrue(response.status_code == 200)
        self.assertIsNone(Wallet.query.first())
