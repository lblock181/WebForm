## https://docs.gunicorn.org/en/stable/settings.html

## Change to expose differnet port
SERVER_PORT = 5555
bind = f'0.0.0.0:{SERVER_PORT}'
backlog = 64

workers = 2
worker_connections = 1000
timeout = 600
keepalive = 5
threads = 4

spew = False

import logging
from gunicorn import glogging

disable_logs_routes = [
    "/static/app.js",
    "/static/favicon.ico",
    "/static/style.css",
]

class CustomGunicornLogger(glogging.Logger):

    def setup(self, cfg):
        super().setup(cfg)

        # Add filters to Gunicorn logger
        logger = logging.getLogger("gunicorn.access")
        logger.addFilter(HealthCheckFilter())

class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return record.args['U'] not in disable_logs_routes


errorlog = '-'
loglevel = 'info'
logger_class = CustomGunicornLogger
accesslog = '-'

access_log_format='%(h)s %(l)s %(t)s %(s)s %(m)s - %(U)s "%(f)s"'
'''
ACCESS LOG FORMAT
Identifier	Description
h	remote address
l	'-'
u	user name
t	date of the request
r	status line (e.g. GET / HTTP/1.1)
m	request method
U	URL path without query string
q	query string
H	protocol
s	status
B	response length
b	response length or '-' (CLF format)
f	referer
a	user agent
T	request time in seconds
M	request time in milliseconds
D	request time in microseconds
L	request time in decimal seconds
p	process ID
{header}i	request header
{header}o	response header
{variable}e	environment variable
'''
capture_output = True
enable_stdio_inheritance = True

proc_name = None

## See https://docs.gunicorn.org/en/stable/settings.html#server-hooks for Server Hooks for custom server handling