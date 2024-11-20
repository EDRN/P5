# flake8: noqa

import multiprocessing

wsgi_app = 'entrypoint:application'
bind = ['0.0.0.0:8000']
preload_app = True
daemon = False

accesslog = '-'
errorlog = '-'
loglevel = 'debug'

# DO NOT ENABLE THIS LINE:
# workers = multiprocessing.cpu_count() * 2 + 1
# WHY?
# IT COMPLETELY MESSES UP django_plotly_dash!



# threads = 
# worker_class = 'gevent'  # TODO: test this out

# TODO: syslog setttings?
