import os
from wsgiref.simple_server import make_server
from cgi import parse_qs, escape

PORT = 8000
PUBLIC = 'public'

def simple_app(environ, start_response):

    print environ['PATH_INFO']
    print environ['QUERY_STRING']

    # Returns a dictionary in which the values are lists
    d = parse_qs(environ['QUERY_STRING'])

    status = '200 OK'
    headers = [('Content-type', 'text/plain')]

    start_response(status, headers)

    ret = ["%s: %s\n" % (key, value)
           for key, value in environ.iteritems()]
    ret = 'hi there'
    return ret

httpd = make_server('', PORT, simple_app)
os.chdir(PUBLIC)

# Respond to requests until process is killed
httpd.serve_forever()
