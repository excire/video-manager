FROM node:20-slim

WORKDIR /frontend

COPY package*.json ./
RUN npm install

COPY . .

CMD ["npm", "run", "dev", "--", "--host"]
