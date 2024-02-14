"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
        
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""
        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    def test_user_is_following(self):
        """ does is_following work?"""

        #create users and have one follow the other
        with app.app_context():
            user1 = User(
                email="test1@test.com",
                username="testuser1",
                password="HASHED_PASSWORD"
            )

            user2 = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )

            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

            follow = Follows(user_being_followed_id = user1.id, user_following_id = user2.id)

            db.session.add(follow)
            db.session.commit()

            self.assertEqual(user2.is_following(user1), True)
            self.assertEqual(user1.is_following(user2), False)
            self.assertEqual(user1.is_followed_by(user2), True)
            self.assertEqual(user2.is_followed_by(user1), False)

    def test_user_creation(self):
        """ does User.signup() work? """

        with app.app_context():
           user3 = User.signup('testuser3','test3@test.com','password', User.image_url.default.arg)

           db.session.commit()

           self.assertEqual(user3.username, 'testuser3')
           with self.assertRaises(TypeError):
               User.signup('user4','testuser4')


    def test_user_authentication(self):
        """ does authentication work? """
        with app.app_context():
           user4 = User.signup('testuser4','test4@test.com','password', User.image_url.default.arg)

           db.session.commit()

           self.assertEqual(User.authenticate('testuser4','password'), user4)
           self.assertEqual(User.authenticate('testuser4','passwor'), False)
           self.assertEqual(User.authenticate('test','password'), False)
