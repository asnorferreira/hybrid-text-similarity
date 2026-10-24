FROM node:24.22.1-bookworm-slim AS dependencies
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
FROM dependencies AS runtime
COPY web ./
COPY contracts /app/contracts
RUN mkdir -p artifacts && chown -R node:node artifacts
RUN npm run build && chown -R node:node .next
USER node
EXPOSE 3000
CMD ["npm", "run", "start"]

FROM dependencies AS browser
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
ENV PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=120000
RUN node node_modules/@playwright/test/cli.js install-deps chromium
RUN node node_modules/@playwright/test/cli.js install --only-shell chromium
COPY web ./
COPY contracts /app/contracts
RUN mkdir -p artifacts && chown -R node:node artifacts
USER node
CMD ["npm", "run", "test:e2e"]
