FROM node:latest
COPY . /opt/build
WORKDIR /opt/build
RUN npm install && npm run build

FROM joseluisq/static-web-server:2-alpine
COPY --from=0 /opt/build/dist ./public
CMD ["--page-fallback", "./public/index.html"]