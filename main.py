import cgi
import urllib
import os
import base64
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import memcache
import webapp2
import random
import string
import settings
# from PIL import Image
DEFAULT_IMAGE_FORMATS = {'width':200,'height':200}

class Profile(ndb.Model):
    """Model with an author, content, avatar, and date."""
    author = ndb.StringProperty()
    content = ndb.TextProperty()
    avatar = ndb.BlobProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

def picture_key(picture_name=None):
    """Constructs a Datastore key with entity name."""
    
    return ndb.Key('Photo', picture_name)

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('<html><body>')
        picture_name = self.request.get('picture_name')

        values = Profile.query(
            ancestor=picture_key(picture_name)) \
            .order(-Profile.date) \
            .fetch(10)

        for value in values:
            if value.author:
                self.response.out.write(
                    '<b>%s</b> wrote:' % value.author)
            else:
                self.response.out.write('An anonymous user:')
            self.response.out.write('<div><img src="/img?img_id=%s"></img>' %
                                    value.key.urlsafe())
            self.response.out.write('<blockquote>%s</blockquote></div>' %
                                     cgi.escape(value.content))

        self.response.out.write("/sign?%s" %(urllib.urlencode({'picture_name': picture_name})))


class Image(webapp2.RequestHandler):
    def get(self):
        value_key = ndb.Key(urlsafe=self.request.get('img_id'))
        value = value_key.get()
        if value.avatar:
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.out.write(value.avatar)
        else:
            self.response.out.write('No image')

class ValueError(Exception):
    """ handles exceptions on width and height """

class Upload(webapp2.RequestHandler):
    def post(self):

        char_set = string.ascii_uppercase + string.digits
        picture_name = ''.join(random.sample(char_set*6, 6))  
        values = Profile.query(
            ancestor=picture_key(picture_name)) \
            .order(-Profile.date) \
            .fetch(10)

        value = Profile(parent=picture_key(picture_name))

        if users.get_current_user():
            value.author = users.get_current_user().nickname()

        value.content = self.request.get('content')        
        avatar = self.request.get ('file')
                
        mimetype = self.request.POST['file'].type
        img_format = mimetype.split('/')[1]

        if (img_format == 'jpeg' or 'jpg'):
            # imageObj = Image.open('avatar')
            imageObj = images.Image (avatar)
            # width = imageObj.width
            # height = imageObj.height
            # print ',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,',imageObj
            im_formats = getattr(settings,'IMAGE_FORMATS',DEFAULT_IMAGE_FORMATS)
            
            width = im_formats['width']
            height = im_formats['height']

            # width  = settings.image_formats['width']
            # height = settings.image_formats['height']

            if not width and not height:
                raise ValueError('height and width must be there')
            if width and height < 0:
                raise ValueError('both width and height must be greater than 0')
            if width > 4000 or height > 4000:
                raise ValueError("Both width and height must be <= 4000.")

            # if width > 100 and height > 100:
            #     raise BadRequestError('both width and height must be less than 1000')
            # if 500 >= width !=0 and 500 >= height !=0 : 
            #     raise BadValue('...........')

            # img=imageObj.resize((width,height),Image.ANTIALIAS)

            # print '^^^^^^^^^^^^^^^^^^###########',img
            avatar = images.resize(avatar,width,height,crop_to_fit=False,allow_stretch=False)
            value.avatar = avatar
            value.put()

            self.redirect('/?' + urllib.urlencode(
            {'picture_name': picture_name}))
            # self.response.out.write ('<html><body>uploaded image is %s x %s [%s] and [url is <href="%s">]</body></html> ' % (width, height, img_format,))
        else:
            self.response.out.write ('not valid format')
        
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/img', Image),
                               ('/upload_image', Upload)],
                              debug=True)