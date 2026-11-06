import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// sql.js 引用了 Node 内置模块，但相关分支在浏览器不会执行；
// 别名到空模块以消除 Vite 的浏览器兼容性警告（/ 开头由 Vite 按项目根解析）。
const emptyShim = "/src/shims/empty-module.ts";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    setupFiles: [],
  },
  esbuild: {
    target: "es2021",
  },
  optimizeDeps: {
    esbuildOptions: {
      target: "es2021",
    },
  },
  resolve: {
    alias: [
      { find: /^fs$/, replacement: emptyShim },
      { find: /^path$/, replacement: emptyShim },
      { find: /^crypto$/, replacement: emptyShim },
    ],
  },
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      // 只预缓存应用图标；public/ 下的大文件（local-backend.zip 约 40 MB、
      // sql-wasm、wasm-golden）改为按需下载，避免每个新访客在后台拉全量资源。
      includeAssets: ["icon-192.svg", "icon-512.svg"],
      manifest: {
        name: "游戏伤害计算器",
        short_name: "计算器",
        description: "多游戏伤害计算器 - AI 辅助创建/查看计算器",
        theme_color: "#1976d2",
        background_color: "#ffffff",
        display: "standalone",
        start_url: "/",
        icons: [
          {
            src: "/icon-192.svg",
            sizes: "192x192",
            type: "image/svg+xml",
          },
          {
            src: "/icon-512.svg",
            sizes: "512x512",
            type: "image/svg+xml",
          },
        ],
      },
      workbox: {
        // 首访只预缓存入口，其余懒加载 chunk/CSS 首次使用时再由 runtimeCaching 缓存。
        globPatterns: ["index.html", "assets/index-*.js"],
        globIgnores: ["**/local-backend.zip", "**/sql-wasm/**", "**/wasm-golden/**"],
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            // 懒加载的页面 chunk、CSS、字体、图标：用后缓存，不在首访预取。
            urlPattern: /\/assets\/.*\.(?:js|css|woff2?|svg|png|ico)$/i,
            handler: "CacheFirst",
            options: {
              cacheName: "app-assets",
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 30,
              },
            },
          },
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24,
              },
            },
          },
          {
            urlPattern: /\/endfield-dag\.json$/i,
            handler: "CacheFirst",
            options: {
              cacheName: "calc-dag",
              expiration: {
                maxEntries: 2,
                maxAgeSeconds: 60 * 60 * 24 * 30,
              },
            },
          },
          {
            urlPattern: /\/api\/data\/(characters|weapons|equipments)\/detail\/all/i,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "game-data-compact",
              expiration: {
                maxEntries: 6,
                maxAgeSeconds: 60 * 60 * 24 * 7,
              },
            },
          },
        ],
      },
    }),
  ],
  build: {
    target: "es2021",
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        // 仅拆出按需加载的重库，避免 react/mui/vendor 循环依赖导致白屏。
        // 不要拆 @xyflow：其 chunk 会连带 React，被入口静态引用后首屏要多下 300+ KB。
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          // 必须按包目录精确匹配：字符串包含 "echarts" 会把 echarts-for-react 也拉进来，
          // 进而把 React 绑定到该 chunk，入口就只能静态引用它（首屏多下 500+ KB）。
          if (/[\\/]node_modules[\\/](?:echarts|zrender)[\\/]/.test(id)) return "echarts";
        },
      },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8180",
        changeOrigin: true,
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // 与 web/run_local.py 默认端口一致
        target: "http://127.0.0.1:8180",
        changeOrigin: true,
      },
    },
  },
});
