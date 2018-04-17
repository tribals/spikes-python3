# from functools import wraps
from wsgiref.simple_server import make_server


def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'It works!']


def main():
    server = make_server('', 5000, app)
    server.serve_forever()


if __name__ == '__main__':
    main()
