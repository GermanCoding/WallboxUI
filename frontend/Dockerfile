FROM node:alpine
COPY . /opt/build
WORKDIR /opt/build
RUN npm install && npm run build

FROM joseluisq/static-web-server:2-alpine
COPY --from=0 /opt/build/dist ./public
COPY --from=0 /opt/build/django-static ./public/static/
CMD ["--page-fallback", "./public/index.html"]