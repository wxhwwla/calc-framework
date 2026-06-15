import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["**/*"],
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
        globPatterns: ["**/*.{js,css,html,json,svg,png,ico,wasm}"],
        navigateFallback: "/index.html",
        runtimeCaching: [
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
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        // 仅拆出按需加载的重库，避免 react/mui/vendor 循环依赖导致白屏
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          if (id.includes("echarts") || id.includes("zrender")) return "echarts";
          if (id.includes("@xyflow")) return "xyflow";
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
