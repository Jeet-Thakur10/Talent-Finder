# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies in a separate layer so they are cached across source changes
COPY package.json package-lock.json ./

RUN npm ci

# Copy the rest of the source
COPY . .

# Build-time environment variable to configure the API base URL
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Stage 2: Serve the compiled static assets with Nginx
FROM nginx:alpine

# Copy the build output to Nginx's html folder
COPY --from=build /app/dist /usr/share/nginx/html

# Expose Nginx default port
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
