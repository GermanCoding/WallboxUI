#!/bin/bash
_term() {
  kill -TERM "$io"
  kill -TERM "$daphne"
}

trap _term SIGTERM

python ./manage.py wait_for_database
python ./manage.py migrate

python ./manage.py wallboxIO &
io=$!

daphne -b 127.0.0.1 backend.asgi:application &
daphne=$!

wait -n
exit $?
