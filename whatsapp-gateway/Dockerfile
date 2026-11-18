FROM node:22-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY index.js ./
ENV HOST=0.0.0.0 PORT=3100 AUTH_DIR=/data/auth
VOLUME /data
EXPOSE 3100
CMD ["node", "index.js"]
