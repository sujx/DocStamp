import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

// Nuxt 客户端构建里 import.meta.client 为 true；vitest 不注入它（define 对
// import.meta.* 不生效），而测试环境本就是非 SSR（import.meta.env.SSR 为 false）。
// 用最小转换插件对齐，使客户端分支在单测里可验证。
function importMetaClientPlugin() {
  return {
    name: "import-meta-client",
    transform(code: string, id: string) {
      if (id.includes("node_modules") || !/\.[cm]?[jt]s$|\.vue$/.test(id)) return null;
      if (!code.includes("import.meta.client")) return null;
      return { code: code.replace(/\bimport\.meta\.client\b/g, "true"), map: null };
    },
  };
}

export default defineConfig({
  plugins: [vue(), importMetaClientPlugin()],
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["**/*.{test,spec}.{ts,js}"],
    exclude: ["node_modules", ".nuxt", "dist"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["composables/**", "components/**"],
    },
  },
  resolve: {
    alias: {
      "~": resolve(__dirname, "."),
      "@": resolve(__dirname, "."),
    },
  },
});
