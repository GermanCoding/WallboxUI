FROM python:slim-bookworm
ENV PYTHONUNBUFFERED=1

RUN apt update && apt install postgresql-client -y --no-install-recommends && mkdir -p /opt/wallbox-ui
WORKDIR /opt/wallbox-ui
# Don't copy everything initially to enable better build caching
COPY ./requirements.txt /opt/wallbox-ui/
RUN pip install --upgrade pip && \
    pip install daphne psycopg2-binary -r requirements.txt

COPY . /opt/wallbox-ui
RUN useradd --system pythonUser --home /opt/wallbox-ui && \
    chown -R pythonUser /opt/wallbox-ui/
USER pythonUser

EXPOSE 8000/tcp
ENTRYPOINT ["/bin/bash"]
CMD ["/opt/wallbox-ui/start.sh"]
