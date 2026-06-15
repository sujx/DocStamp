export default defineNuxtConfig({
  modules: [
    // Nuxt UI v2 内部 safelist 用 'primary' 生成正则但 Tailwind 只认 'green'，
    // safelistColors: ["green"] 让模式匹配到实际生成的 text-green-400 等类名
    ["@nuxt/ui", { safelistColors: ["green"] }],
    "@nuxtjs/i18n",
    "@nuxt/icon",
  ],

  devtools: { enabled: true },

  css: ["~/assets/css/main.css"],

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
