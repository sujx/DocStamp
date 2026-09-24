export default defineNuxtConfig({
  modules: [
    // Nuxt UI v2 safelists the color it resolves from ui.primary; Tailwind must
    // also generate those classes, so the name has to match tailwind.config.ts.
    ["@nuxt/ui", { safelistColors: ["brand"] }],
    "@nuxtjs/i18n",
    "@nuxt/icon",
  ],

  devtools: { enabled: true },

  css: ["~/assets/css/main.css"],

  // 生产是纯静态产物（Flask 托管 .output/public），Nitro 的 /api/_nuxt_icon 路由不存在：
  // 只靠 SSR 内联的图标 CSS，交互后才出现的图标（工具面板、标记列表、按钮内图标）会静默丢字形。
  // 扫源码把用到的图标打进客户端包；Nuxt UI 组件自带的图标不在项目源码里，扫描扫不到，点名带上。
  icon: {
    clientBundle: {
      scan: true,
      icons: [
        "heroicons:chevron-down-20-solid", // USelect 的下拉箭头
        "heroicons:arrow-path-20-solid", // UButton 的 loading 转圈
        "heroicons:x-mark-20-solid", // UNotification 的关闭按钮
      ],
    },
  },


  devServer: {
    port: 8080,
    host: "0.0.0.0",
  },

  runtimeConfig: {
    public: {
      apiBase: "/api/v1",
    },
  },

  vite: {
    define: {
      "globalThis.__unifont_providers": JSON.stringify(["local"]),
    },
    build: {
      splitChunks: true,
    },
    server: {
      proxy: {
        "/api": {
          target: "http://localhost:5000",
          changeOrigin: true,
        },
      },
    },
  },

  i18n: {
    strategy: "no_prefix",
    defaultLocale: "zh-CN",
    locales: [
      { code: "zh-CN", name: "中文", file: "zh-CN.json" },
      { code: "en", name: "English", file: "en.json" },
    ],
    lazy: false,
    bundle: { optimizeTranslationDirective: false },
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: "docstamp_lang",
      alwaysRedirect: false,
      fallbackLocale: "zh-CN",
    },
  },


  nitro: {
    prerender: {
      crawlLinks: true,
      concurrency: 1,         // Serial prerender — prevents OOM on 2GB machines
      failOnError: false,     // Skip pages that fail, don't abort the build
    },
  },
  compatibilityDate: "2026-06-06",
});
