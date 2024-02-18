"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY, do_login

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()


app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """ Test views for users """

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)
            db.session.commit()

            #create test message by test user

            msg = Message(text = 'Hello',
                            user_id = self.testuser.id)
            
            #create user following test user

            following_me = User(
                email="test1@test.com",
                username="following_me",
                password="HASHED_PASSWORD"
            )

            #create user for test user to follow

            im_following_this= User(
                email="test2@test.com",
                username="im_following",
                password="HASHED_PASSWORD"
            )

            db.session.add(following_me)
            db.session.add(im_following_this)            
            db.session.add(msg)        
            db.session.commit()    

            follow_me = Follows(user_being_followed_id = self.testuser.id, user_following_id = following_me.id)

            i_follow = Follows(user_being_followed_id = im_following_this.id, user_following_id = self.testuser.id)

            db.session.add(follow_me)
            db.session.add(i_follow)
            db.session.commit()

    def test_view_users(self):
        """ can we view users"""

        with self.client as c:
            resp =c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser',html)

    def test_view_users_search(self):
        """ can we search users"""

        with self.client as c: 
            resp = c.get('/users', query_string = {'q': 'test'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser',html)

    def test_view_user_profile(self):
        """ can we view profiles """

        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser', html)
            self.assertIn('Hello', html)

    def test_loggedin_show_following(self):
        """ can we view following page while logged in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('im_following',html)

    def test_loggedout_show_following(self):
        """ are we redirected and flashed if we attemt to view following page while logged out"""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.',html)

    def test_loggedin_show_followers(self):
        """ can we view followers page while logged in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('following_me',html)

    def test_loggedout_show_followers(self):
        """ are we redirected and flashed if we attemt to view followers page while logged out"""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.',html)
