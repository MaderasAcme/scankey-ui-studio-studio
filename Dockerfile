FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app

COPY web-server/package.json /app/web-server/package.json
RUN cd /app/web-server && npm install --omit=dev

COPY web-server/server.js /app/web-server/server.js
COPY --from=build /app/dist /app/dist

ENV PORT=8080
EXPOSE 8080
CMD ["node", "/app/web-server/server.js"]
