import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
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
