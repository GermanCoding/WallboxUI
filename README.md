# Wallbox UI

### Overview

This is a web interface designed to extract information from a Keba KeContact P30 Wallbox.
It was originally designed to enhance an existing P30 c-series
(which does not have a "real" management interface by themselves) it may also prove useful
for other series of the P30 wallbox models.

The idea is that you run this web interface on a small appliance (a server, as raspbery PI, a NAS...) which provides you
with real-time data about your wallbox.

### Features

- Retrieve charge session logs from the wallbox for long-term storage, display and backup
    - Supports all information provided by the Keba UDP protocol: Session start/stop times, charged energy, energy meter
      at start, charging current, stop reason, RFID authorization code
- Export of charge sessions as csv (e.g. for billing)
- Status display of wallbox displaying current information (eletrical information, current charge status, energy meter,
  cable and system status, and more)
- Security by default: Includes and requires authentication out of the box
    - Secured admin-only access for user management

### Deployment (production)

Deploying this should be mostly straightforward. The
reference deployment currently uses docker-compose. You can deploy this
via alternate means as well - I suggest reading through the development documentation
to get a grip on how stuff works.

For docker-compose, the following things need to be done:

1. Clone this repository to your local disk, if you haven't already (refer to git clone for details).
2. Add configuration:
    - The included compose file loads configuration from a `config.env` file (for backend configuration) and
      a `db.env` (for database configuration) by default.

      A configuration file may look like this:

      ``config.env``
        ```
        WALLBOX_IP=<IP address of your wallbox>
        DEBUG=False
        # You need to manually manage HTTPS via a reverse proxy
        HTTPS=True
        # The default docker compose spins up a postgres db
        DB=postgres
        DB_HOST=db
        DB_NAME=<your DB name>
        DB_USER=postgres
        DB_PASSWORD=<your DB password>
        ALLOWED_HOSTS=<domain name you're hosting the web UI at>
        CSRF_TRUSTED_ORIGINS=https://<domain name you're hosting the web UI at>
        # Approx 2 seconds on a raspberry pi 3. Increase if you have more computational power.
        # Larger values increase security against bruteforce password cracking attacks, but slow down logins
        HASH_ITERATIONS=180000
        # This URL gets called (HTTP GET) (at least) every hour if wallbox communcation was succesful. Useful for uptime monitoring
        HEALTHCHECK_URL=<my monitoring URL>
        ```

      The docker compose file also spins up a postgres db. Configure (at least) its database name and password (default user
      is postgres).
      Refer to the official postgres docker image documentation for more information.

      ``db.env``
      ```
      POSTGRES_DB=<your DB name>
      POSTGRES_PASSWORD=<your DB password>
      ```
3. Spin up containers: `docker compose up -d --build` (or docker-compose if using the standalone tool instead of the
   plugin).
    - This will (re-)build the containers and spin them up.
    - Verify that stuff is running via the usual `docker ps`, `docker logs` etc commands. You should see 3 containers:
        - The database container
        - The backend container (containing a django python server and a python script). This container should indicate
          successful database connection and communication with the wallbox.
        - A static web server hosting the vue.js frontend
4. Configure a reverse proxy:
    - The reverse proxy can be pretty much anything you like (nginx, Apache, Traefik, caddy...).
      An example nginx configuration is further down below. In any case, you most provide the following:
        - Your reverse proxy must provide https (you may get away with setting HTTPS=False in your config and using
          plain HTTP, but I don't support that use case). Some reverse proxies like caddy provide https out of the box.
          Let's Encrypt provides free certificates for everything.
        - You must forward requests to the prefixes `/admin` and `/api` to the backend webserver (listening on
          127.0.0.1:8000 in the default docker compose). All other path prefixes must be forwarded to the frontend
          webserver (listening on 127.0.0.1:8001 in the default docker compose).

      Example nginx config (minimal, not really suitable for production):
    ```
    server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name <my domain name>;
    ssl_certificate <my ssl cert>;
    ssl_certificate_key <my ssl key>;
    
    location / {
        proxy_set_header Host $host;
        proxy_pass http://127.0.0.1:8001$request_uri;
    }
    
    location /admin {
        proxy_set_header Host $host;
        proxy_pass http://127.0.0.1:8000$request_uri;
    }
    
    location /api {
        proxy_set_header Host $host;
        proxy_pass http://127.0.0.1:8000$request_uri;
    }
    }
    ```
5. Create an initial superuser account: The application always requires authentication, so you need credentials. Run
   ``docker exec -it <backend container name> python ./manage.py createsuperuser``. You can find out the backend's
   container name with ``docker ps``. You can now log in using these credentials.

### Development

#### Project architecture overview

- backend: Contains a python django project. This hosts the main application logic, communicates with the wallbox and
  provides a REST API.
- frontend: Contains a vuetify/vue.js project. This is an example graphical frontend that communicates with the REST API
  of the backend.

#### Running development builds

1. Prepare and run the django server:
    - **one time only** ``pip install -r requirements.txt`` (consider doing this in a python venv if you know how)
    - ``./manage.py runserver`` (from within the backend directory)
2. Prepare and run the vite frontend development server:
    - **one time only** ``npm install`` (requires node.js installed)
    - ``npm run dev``
3. Done! (Development setup is deliberately fast. Please note that **insecure** defaults are used since no configuration
   is given. A default sqlite database will be used for data).
4. If needed, create a new admin account: ``./manage.py createsuperuser`` (from within the backend directory).
5. If you want your development instance to communicate with the wallbox, you need to run ``./manage.py wallboxIO``.
   This requires the wallbox IP address to be provided via enviroment variable, ``WALLBOX_IP``.

### Caveats

- While the backend is language neutral already, the frontend is currently hardcoded to german i18n. Full localization
  support would be welcome.
- Missing tests

### Disclaimer

This project is not affiliated with or supported by © KEBA in any way.
