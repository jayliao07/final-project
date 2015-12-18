import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2
import time


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# Models
####################################################################################
class Reservation(ndb.Model):
    """Models an reservation create by an user"""
    book_person = ndb.StringProperty(required=True, indexed=True) # eamil
    resource_id = ndb.IntegerProperty()
    resource_name = ndb.StringProperty()
    avail_date = ndb.StringProperty(indexed=True)
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    start_time = ndb.IntegerProperty(indexed=True)
    end_time = ndb.IntegerProperty(indexed=True)

class Resource(ndb.Model):
    """Models an resource create by an owner"""
    owner = ndb.StringProperty(required=True, indexed=True) # email
    resource_name = ndb.StringProperty(required=True, indexed=True)
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    avail_date = ndb.StringProperty(indexed=True)
    start_time = ndb.IntegerProperty(indexed=True)
    end_time = ndb.IntegerProperty(indexed=True)
    reservations = ndb.StructuredProperty(Reservation, repeated=True)
    tags = ndb.StringProperty(repeated=True, indexed=True)


# Handlers
####################################################################################
class MainPage(webapp2.RequestHandler):
    """
    Main page Handlers
    """
    def get(self):
        user = users.get_current_user()
        # if user is logged in
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Sign out'
            user_email = user.email()
            all_resources = Resource.gql("ORDER BY created_date DESC")
            user_resources = Resource.gql("WHERE owner = :1 ORDER BY created_date DESC",
                         user_email)
            user_reservations = Reservation.gql("WHERE book_person = :1 ORDER BY start_time",
                         user_email)

            # uid = user.user_id() 
            template_values = {
                'user': user,
                'url': url,
                'url_linktext': url_linktext,
                'user_email': user_email,
                'all_resources':all_resources,
                'user_resources':user_resources,
                'user_reservations': user_reservations,
            }

        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Sign in'
            user_email = 'New Guest'
            # uid = -1

            template_values = {
                'user': user,
                'url': url,
                'url_linktext': url_linktext,
                'user_email': user_email,
            }

        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render(template_values))

class CreateResource(webapp2.RequestHandler):
    # show the web page for creating resource
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/create_resource.html')
        self.response.write(template.render())

    # create new resource and return to main page
    def post(self):
        start_time = int(self.request.get('stime'))
        end_time = int(self.request.get('etime'))
        if start_time >= end_time:
            template = JINJA_ENVIRONMENT.get_template('templates/error.html')
            self.response.write(template.render({'message': "End time must be greater than Start"}))
        else:
            new_res = Resource()
            new_res.owner = users.get_current_user().email()
            new_res.resource_name = self.request.get('name')
            new_res.avail_date = self.request.get('date')
            new_res.start_time = start_time
            new_res.end_time = end_time
            new_res.tags = str(self.request.get('tags')).split(',')
            new_res.put()
            time.sleep(0.1)
            self.redirect('/')

class ShowResource(webapp2.RequestHandler):
    # show the web page for resource
    def get(self):
        user = users.get_current_user()

        resource_id = int(self.request.get('resource_id'))
        resource=Resource.get_by_id(resource_id)
        reservations=Reservation.gql("WHERE resource_id = :1 ORDER BY start_time",
                         resource_id)

        canEdit = False
        if user.email() == resource.owner:
            canEdit = True

        template_values = {
            'resource': resource,
            'canEdit': canEdit,
            'reservations': reservations,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/show_resource.html')
        self.response.write(template.render(template_values))

    # create new reservation
    def post(self):
        reser_button = self.request.get('reser-btn')
        edit_button = self.request.get('edit-btn')

        if reser_button:
            start_time = int(self.request.get('stime'))
            end_time = int(self.request.get('etime'))
            if start_time >= end_time:
                template_values = {
                    'message': "End time must be greater than Start and New Reservation cannot confilct with old ones."
                }
                template = JINJA_ENVIRONMENT.get_template('templates/error.html')
                self.response.write(template.render(template_values))
            else:
                new_reserv = Reservation()
                new_reserv.start_time = start_time
                new_reserv.end_time = end_time
                new_reserv.book_person = users.get_current_user().email()

                resouce_id = int(self.request.get('resouId'))
                resource = Resource.get_by_id(resouce_id)
                new_reserv.resource_name = resource.resource_name
                new_reserv.resource_id = resouce_id
                new_reserv.avail_date = resource.avail_date
                new_reserv.put()
                resource.reservations.append(new_reserv)

                time.sleep(0.5)
                self.redirect('/')
        if edit_button:
            template = JINJA_ENVIRONMENT.get_template('templates/error.html')
            self.response.write(template.render({'message': "Debug"}))
            start_time = int(self.request.get('stime'))
            end_time = int(self.request.get('etime'))
            if start_time >= end_time:
                template = JINJA_ENVIRONMENT.get_template('templates/error.html')
                self.response.write(template.render({'message': "End time must be greater than Start"}))
            else:
                resouce_id = int(self.request.get('resouId'))
                cur = Resource.get_by_id(resouce_id)
                cur.resource_name = self.request.get('name')
                cur.avail_date = self.request.get('date')
                cur.start_time = int(self.request.get('stime'))
                cur.end_time = int(self.request.get('etime'))
                cur.tags = str(self.request.get('tags')).split(',')
                cur.put()

                time.sleep(0.1)
                self.redirect('/')


class DeleteReservation(webapp2.RequestHandler):
    def get(self):
        cur_id = int(self.request.get('reser_id'))
        cur = Reservation.get_by_id(cur_id)
        cur.key.delete()

        time.sleep(0.2)
        self.redirect('/')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/createResource', CreateResource),
    ('/resource', ShowResource),
    ('/deleteReserv', DeleteReservation)
], debug=True)
