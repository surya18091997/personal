# Dockerfile for React service

# Use the official Node.js image as the base image
FROM node:16 as build

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the application code to the working directory
COPY . .

# Build the React application
RUN npm run build


FROM nginx:1.22.1

WORKDIR /usr/share/nginx/html

RUN rm /etc/nginx/conf.d/*

RUN rm -rf /usr/share/nginx/html/*

COPY --from=build /app/build/ /usr/share/nginx/html

COPY --from=build /app/nginx/default.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
