FROM node:22.9-bookworm

WORKDIR /webapp

COPY package.json yarn.lock ./

RUN yarn install --frozen-lockfile
RUN yarn global add serve

COPY tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./

COPY public/ ./public
COPY src/ ./src
COPY index.html ./

# Build the app in production mode
RUN yarn build

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]