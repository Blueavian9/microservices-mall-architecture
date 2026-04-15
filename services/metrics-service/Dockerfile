FROM node:20-alpine

WORKDIR /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY package.json ./
RUN npm install --omit=dev

COPY src/ ./src/

USER appuser
EXPOSE 3002

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD wget -qO- http://localhost:3002/health || exit 1

CMD ["node", "src/index.js"]
