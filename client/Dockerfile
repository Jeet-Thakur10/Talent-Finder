FROM node:20-alpine

WORKDIR /app

# Install dependencies in a separate layer so they are cached across source changes
COPY package.json package-lock.json ./

RUN npm ci

# Copy the rest of the source
COPY . .

EXPOSE 5173

# --host 0.0.0.0 is required so the Vite dev server binds on all interfaces
# inside the container and is reachable from the published host port
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
