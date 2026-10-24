FROM node:24.22.1-bookworm-slim
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
COPY contracts /app/contracts
RUN npm run build && chown -R node:node .next
USER node
EXPOSE 3000
CMD ["npm", "run", "start"]
