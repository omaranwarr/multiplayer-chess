FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/vite.config.js ./
COPY frontend/src ./src
COPY frontend/index.html ./
RUN npm install && npm run build

FROM python:3.9-slim

WORKDIR /app

COPY chess-app/requirements.txt .
RUN pip install -r requirements.txt

COPY chess-app/ .

COPY --from=frontend-builder /frontend/dist ./static/frontend

# Fix Vite's generated index.html to use Django static paths
# Replace /assets/ with /static/frontend/assets/ in the built index.html
RUN sed -i 's|href="/assets/|href="/static/frontend/assets/|g; s|src="/assets/|src="/static/frontend/assets/|g' static/frontend/index.html && \
    cp static/frontend/index.html templates/index.html

# Set up database and collect static files
RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chess_project.asgi:application"]