# ==============================================================================
# AIR_Memory Frontend Dockerfile
# 多阶段构建：Node.js 构建 Vue.js 3 静态文件，Nginx 提供服务
# ==============================================================================

# ---------- 构建阶段 ----------
FROM node:20-alpine AS builder

WORKDIR /app

# 先拷贝依赖文件以利用 Docker 构建缓存
COPY package*.json ./
RUN npm ci

# 拷贝源码并构建
COPY . .
RUN npm run build

# ---------- 服务阶段 ----------
FROM nginx:1.27-alpine

# 拷贝构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 拷贝 Nginx 配置（反向代理 /api/ 到 backend）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露服务端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
