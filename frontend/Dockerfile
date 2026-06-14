# Build the SPA, then serve it with nginx which also reverse-proxies /api → API_URL.
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV API_URL=http://localhost:8000 \
    PORT=8080
EXPOSE 8080
