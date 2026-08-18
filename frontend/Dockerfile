FROM node:20-alpine AS base
WORKDIR /app

COPY package.json package-lock.json* ./
# Sekin/beqaror tarmoqda ECONNRESET bo'lmasligi uchun retry/timeout oshirilgan;
# yuklab bo'lingan paketlar npm keshida qoladi, shuning uchun butun
# "npm install"ni bir necha marta qayta urinish xavfsiz va tezroq yakunlanadi.
RUN npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm config set fetch-timeout 300000 \
    && for i in 1 2 3 4 5; do npm install && break || { echo "npm install urinish $i muvaffaqiyatsiz, qayta urinilmoqda..."; sleep 10; }; done

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
