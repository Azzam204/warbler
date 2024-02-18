"""Message View tests."""

# run these tests like:
#
#    python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            User.query.delete()
            Message.query.delete()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)
            u = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)            
            db.session.commit()

    def test_add_message(self):
        """Can use add a message while logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_for_other_user(self):
        """Do we prevent add a message for different user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "test add to other user", "user_id" : 2})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            messages = Message.query.filter_by(user_id = self.testuser.id).all()

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].text, "test add to other user")

    def test_add_message_loggedout(self):
        """Do we prohibit adding a message while logged out?"""

        with self.client as c:

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.',html)

    def test_view_message(self):
        """ can we view message details """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # create new message 
            with app.app_context():
                msg = Message(text = 'Hello',
                            user_id = self.testuser.id)
                
                db.session.add(msg)
                db.session.commit()
            
            # get message details page

            resp = c.get(f'/messages/{msg.id}')
            html = resp.get_data(as_text = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Hello', html)

    def test_delete_message(self):
        """ can we delete message while logged in? """
    
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # create new message 
            with app.app_context():
                msg = Message(text = 'Hello',
                            user_id = self.testuser.id)
                
                db.session.add(msg)
                db.session.commit()

            # post request to delete message
            resp = c.post(f'/messages/{msg.id}/delete', follow_redirects=True)
            html =resp.get_data(as_text= True)

            # Test redirect
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Message deleted', html)

            messages = Message.query.filter_by(user_id = self.testuser.id).all()

            self.assertEqual(len(messages), 0)

    def test_delete_message_for_other_user(self):
        """Do we prevent delete message for other users? """
    
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # create new user and message for new user
            with app.app_context():

                u = User(
                    email="test3@test.com",
                    username="testuser3",
                    password="HASHED_PASSWORD"
                )

                db.session.add(u)            
                db.session.commit()

                msg = Message(text = 'other user message',
                            user_id = u.id)
                
                db.session.add(msg)
                db.session.commit()

            # get request to delete message
            resp = c.get(f'/messages/{msg.id}/delete', follow_redirects=True)
            html =resp.get_data(as_text= True)

            # Test redirect
            self.assertEqual(resp.status_code, 405)
            self.assertIn('Method Not Allowed', html)

            messages = Message.query.filter_by(text = 'other user message').all()

            self.assertEqual(len(messages), 1)

    def test_delete_message_loggedout(self):
        """ Do we prohibit delete message while logged out? """
    
        with self.client as c:

            # create new message 
            with app.app_context():
                msg = Message(text = 'Hello',
                            user_id = self.testuser.id)
                
                db.session.add(msg)
                db.session.commit()

            # post request to delete message
            resp = c.post(f'/messages/{msg.id}/delete', follow_redirects=True)

            html =resp.get_data(as_text= True)

            # Test redirect
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.',html)

