import json
import unittest
from base64 import b64encode
from datetime import datetime

from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash

from app import create_app, db
from app.models import User, Role


class UserTestCase(unittest.TestCase):

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

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create new user
        new_user = User.from_json(
            {'username': 'test_user',
             'email': 'test_user@example.com',
             'password': 'new_password',
             'confirmed': True,
             'first_name': 'test_first_name',
             'last_name': 'test_last_name'}
        )
        db.session.add(new_user)
        db.session.commit()

        # Login new_user
        response = self.client.post(
            url_for('api.login'),
            headers=self.get_api_headers('test_user', 'new_password')
        )

        self.token = response.json['token']

        self.data = {'username': 'test_user2',
                     'email': 'user2@example.com',
                     'password': 'password2',
                     'confirmed': True,
                     'first_name': 'test_first_name',
                     'last_name': 'test_last_name'}

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
        """
        The test case for create_user view.
        """
        response = self.client.post(
            url_for('api.create_user'),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )

        self.assertTrue(response.status_code == 201)
        self.assertTrue(response.json['username'] == self.data['username'])
        self.assertTrue(response.json['email'] == self.data['email'])
        self.assertTrue(check_password_hash(response.json['password'], self.data['password']))
        self.assertTrue(response.json['confirmed'] == self.data['confirmed'])
        self.assertTrue(response.json['first_name'] == self.data['first_name'])
        self.assertTrue(response.json['last_name'] == self.data['last_name'])

    def test_update_user(self):
        """
        The test case for update_user view.
        """
        user = User.query.first()
        print(user)
        response = self.client.put(
            url_for('api.update_user', id=user.id),
            headers=self.get_token_headers(self.token),
            data=json.dumps(self.data)
        )
        print(response.json)
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.json['username'] == self.data['username'])
        self.assertTrue(response.json['email'] == self.data['email'])
        self.assertTrue(check_password_hash(response.json['password'], self.data['password']))
        self.assertTrue(response.json['confirmed'] == self.data['confirmed'])
        self.assertTrue(response.json['first_name'] == self.data['first_name'])
        self.assertTrue(response.json['last_name'] == self.data['last_name'])