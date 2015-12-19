import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import mail

import jinja2
import webapp2
from datetime import datetime
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
    avail_date = ndb.DateProperty(indexed=True)
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    start_time = ndb.IntegerProperty(indexed=True)
    end_time = ndb.IntegerProperty(indexed=True)

class Resource(ndb.Model):
    """Models an resource create by an owner"""
    owner = ndb.StringProperty(required=True, indexed=True) # email
    resource_name = ndb.StringProperty(required=True, indexed=True)
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    avail_date = ndb.DateProperty(indexed=True)
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
            user_resources = Resource.gql("WHERE owner = :1 ORDER BY created_date DESC", user_email)

            today = datetime.now()
            # only show reservations after today's date
            user_reservations = Reservation.gql("WHERE book_person = :1 AND avail_date >= :2 ORDER By avail_date",
                         user_email, today)
            all_tags = sorted(set([j for i in all_resources for j in i.tags]))

            search_tag = self.request.get('tag')
            search_name = self.request.get('search_name')

            if search_tag:
                all_rs = []
                user_rs = []
                for r in all_resources:
                    if search_tag in r.tags:
                        all_rs.append(r)
                for r in user_resources:
                    if search_tag in r.tags:
                        user_rs.append(r)
                all_resources = all_rs
                user_resources = user_rs

            if search_name:
                all_resources = Resource.gql("WHERE resource_name = :1 ORDER BY created_date DESC", search_name)

            template_values = {
                'user': user,
                'url': url,
                'url_linktext': url_linktext,
                'user_email': user_email,
                'all_resources':all_resources,
                'user_resources':user_resources,
                'user_reservations': user_reservations,
                'all_tags': all_tags
            }

        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Sign in'
            user_email = 'New Guest'

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
        try:
            avail_date = datetime.strptime(self.request.get('date'), '%Y-%m-%d')
            start_time = int(self.request.get('stime'))
            end_time = int(self.request.get('etime'))
            today = datetime.now()
            if start_time >= end_time:
                template = JINJA_ENVIRONMENT.get_template('templates/error.html')
                self.response.write(template.render({'message': "End time must be greater than Start"}))
            elif avail_date < today:
                template = JINJA_ENVIRONMENT.get_template('templates/error.html')
                self.response.write(template.render({'message': "The date should after Now"}))
            else:
                new_res = Resource()
                new_res.owner = users.get_current_user().email()
                new_res.resource_name = self.request.get('name')
                new_res.avail_date = avail_date
                new_res.start_time = start_time
                new_res.end_time = end_time
                tags = self.request.get('tags')
                new_res.tags = tags.split()
                new_res.put()
                time.sleep(0.1)
                self.redirect('/')
        except ValueError:
            template = JINJA_ENVIRONMENT.get_template('templates/error.html')
            self.response.write(template.render({'message': "Please enter correct date format as year-mm-dd"}))

class ShowResource(webapp2.RequestHandler):
    # show the web page for resource
    def get(self):
        user = users.get_current_user()

        resource_id = int(self.request.get('resource_id'))
        resource=Resource.get_by_id(resource_id)
        reservations=Reservation.gql("WHERE resource_id = :1 ORDER BY start_time", resource_id)

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
            resource_id = int(self.request.get('resouId'))
            resource = Resource.get_by_id(resource_id)
            template = JINJA_ENVIRONMENT.get_template('templates/error.html')

            if start_time >= end_time:    
                self.response.write(template.render({'message': "End time must be greater than Start"}))
            elif start_time<resource.start_time or end_time>resource.end_time:
                self.response.write(template.render({'message': "Reservation must made within resource time range"}))
            else:
                prev_reservations = Reservation.gql("WHERE resource_id = :1", resource_id)
                # self.response.write(template.render({'message': prev_reservations }))
                for p in prev_reservations:
                    if not (start_time>=p.end_time or end_time<=p.start_time):
                        self.response.write(template.render({'message': "Reservation cannot conflict with previous ones."}))
                        return
                new_reserv = Reservation()
                new_reserv.start_time = start_time
                new_reserv.end_time = end_time
                new_reserv.book_person = users.get_current_user().email()

                new_reserv.resource_name = resource.resource_name
                new_reserv.resource_id = resource_id
                new_reserv.avail_date = resource.avail_date
                new_reserv.put()

                time.sleep(0.3)
                self.redirect('/')
        if edit_button:
            try:
                avail_date = datetime.strptime(self.request.get('date'), '%Y-%m-%d')
                start_time = int(self.request.get('stime'))
                end_time = int(self.request.get('etime'))
                today = datetime.now()
                if start_time >= end_time:
                    template = JINJA_ENVIRONMENT.get_template('templates/error.html')
                    self.response.write(template.render({'message': "End time must be greater than Start"}))
                elif avail_date < today:
                    template = JINJA_ENVIRONMENT.get_template('templates/error.html')
                    self.response.write(template.render({'message': "The date should after Now"}))
                else:
                    resource_id = int(self.request.get('resouId'))
                    cur = Resource.get_by_id(resource_id)
                    cur.resource_name = self.request.get('name')
                    cur.avail_date = avail_date
                    cur.start_time = int(self.request.get('stime'))
                    cur.end_time = int(self.request.get('etime'))
                    cur.tags = self.request.get('tags').split()
                    cur.put()
                    time.sleep(0.3)
                    self.redirect('/')
            except ValueError:
                template = JINJA_ENVIRONMENT.get_template('templates/error.html')
                self.response.write(template.render({'message': "Please enter correct date format as year-mm-dd"}))

class ShowUser(webapp2.RequestHandler):
    # show the web page for a user
    def get(self):
        user_email = self.request.get('email')

        resources=Resource.gql("WHERE owner = :1 ORDER BY created_date DESC", user_email)
        today = datetime.now()
        # only show reservations after today's date
        reservations = Reservation.gql("WHERE book_person = :1 AND avail_date >= :2 ORDER By avail_date",
                         user_email, today)

        template_values = {
            'user_email': user_email,
            'resources': resources,
            'reservations': reservations,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/show_user.html')
        self.response.write(template.render(template_values))

class DeleteReservation(webapp2.RequestHandler):
    def get(self):
        cur_id = int(self.request.get('reser_id'))
        cur = Reservation.get_by_id(cur_id)
        cur.key.delete()
        time.sleep(0.3)
        self.redirect('/')

class RSS(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        resource_id = int(self.request.get('resource_id'))
        resource=Resource.get_by_id(resource_id)
        reservations=Reservation.gql("WHERE resource_id = :1 ORDER BY start_time", resource_id)

        template_values = {
            'user': user,
            'resource': resource,
            'reservations': reservations
        }

        template = JINJA_ENVIRONMENT.get_template('templates/rss.html')
        self.response.headers['Content-Type'] = "text/xml; charset=utf-8"
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/tag', MainPage),
    ('/createResource', CreateResource),
    ('/resource', ShowResource),
    ('/user', ShowUser),
    ('/deleteReserv', DeleteReservation),
    ('/rss', RSS)
], debug=True)
