FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --dev
COPY . .
CMD ["npm", "start"]