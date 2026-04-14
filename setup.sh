#!/bin/bash
set -e

# 1. Root Setup
pnpm init
cat << 'YAML' > pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
YAML

# 2. Shared Types Package
mkdir -p packages/shared-types/src
cd packages/shared-types
pnpm init
# Modify package.json to have correct name and main
sed -i '' 's/"name": "shared-types"/"name": "@histree\/shared-types"/' package.json
sed -i '' 's/"main": "index.js"/"main": "src\/index.ts"/' package.json
cd ../..

# 3. Backend (NestJS)
mkdir -p apps
cd apps
npx -y @nestjs/cli new api --strict --package-manager pnpm --skip-git --skip-install

# Scaffold API Modules
cd api
mkdir -p src/modules/{event,person,graph,timeline}
cd ../..

# 4. Frontend (React + Vite)
cd apps
npx -y create-vite web --template react-ts
cd web
# Add shared-types as dependency
pnpm add @histree/shared-types --workspace
pnpm add d3
pnpm add -D @types/d3
cd ../..

