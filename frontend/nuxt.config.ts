export default defineNuxtConfig({
  modules: ["@nuxt/ui", "@nuxtjs/i18n", "@nuxt/icon"],

  devtools: { enabled: true },

  css: ["~/assets/css/main.css"],

  devServer: {
    port: 8080,
    host: "0.0.0.0",
  },

  runtimeConfig: {
    public: {
      apiBase: "/api",
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

  // @nuxtjs/i18n v8 config (Nuxt 3 compatible)
  i18n: {
    strategy: "no_prefix",
    defaultLocale: "zh-CN",
    locales: [
      { code: "zh-CN", name: "中文", file: "zh-CN.json" },
      { code: "en", name: "English", file: "en.json" },
    ],
    lazy: true,
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: "docstamp_lang",
      alwaysRedirect: false,
      fallbackLocale: "zh-CN",
    },
  },

  ssr: false,

  compatibilityDate: "2026-06-06",
});
