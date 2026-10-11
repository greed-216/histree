FROM node:24-bookworm-slim AS builder

# Enable pnpm
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ && rm -rf /var/lib/apt/lists/*
RUN corepack enable pnpm

WORKDIR /app

# Copy workspace configuration
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy packages and api app
COPY packages/shared-types ./packages/shared-types
COPY apps/api ./apps/api
COPY apps/web ./apps/web

# Install dependencies
RUN pnpm install --frozen-lockfile

# Same-origin frontend and API; secrets belong only in runtime.env.
ENV VITE_API_URL=/api/v1 VITE_ASK_API_URL=/api/v1
RUN pnpm --filter @histree/shared-types build
RUN pnpm --filter web build
RUN pnpm --filter api build
RUN pnpm --filter api deploy --prod --legacy /runtime

FROM node:24-bookworm-slim AS runner

WORKDIR /app
ARG HISTREE_REVISION
LABEL org.opencontainers.image.revision=$HISTREE_REVISION

# Includes only API production dependencies, compiled API and dsh resources.
COPY --from=builder --chown=node:node /runtime ./apps/api
COPY --from=builder --chown=node:node /app/apps/web/dist ./apps/web/dist
ENV NODE_ENV=production HISTREE_WEB_ROOT=/app/apps/web/dist

USER node
EXPOSE 3000

# Start the NestJS application
CMD ["node", "apps/api/dist/main.js"]
