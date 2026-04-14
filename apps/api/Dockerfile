FROM node:20-alpine AS builder

# Enable pnpm
RUN corepack enable pnpm

WORKDIR /app

# Copy workspace configuration
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy packages and api app
COPY packages/shared-types ./packages/shared-types
COPY apps/api ./apps/api

# Install dependencies
RUN pnpm install --frozen-lockfile

# Build the shared types and the API
RUN pnpm --filter @histree/shared-types... build || true
RUN pnpm --filter api build

FROM node:20-alpine AS runner

WORKDIR /app

# Copy built assets and node_modules from builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/packages/shared-types ./packages/shared-types
COPY --from=builder /app/apps/api/node_modules ./apps/api/node_modules
COPY --from=builder /app/apps/api/dist ./apps/api/dist
COPY --from=builder /app/apps/api/package.json ./apps/api/package.json

EXPOSE 3000

# Start the NestJS application
CMD ["node", "apps/api/dist/main.js"]
