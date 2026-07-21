# Build from the frontend directory:
# docker build --build-arg API_BASE_URL=http://host.docker.internal:8000/api/v1 -t dress-rental-frontend .

FROM nginx:1.27-alpine

# The API base URL is baked into the static config file during image build.
ARG API_BASE_URL=http://localhost:8000/api/v1

WORKDIR /usr/share/nginx/html

# Copy only the static frontend files into Nginx's document root.
COPY index.html styles.css app.js config.js ./

# Replace the development URL in config.js with the supplied backend URL.
RUN sed -i "s|const API_BASE_URL = \".*\";|const API_BASE_URL = \"${API_BASE_URL}\";|" config.js

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
