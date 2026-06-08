module.exports = {
  root: true,
  extends: ["@nuxtjs/eslint-config-typescript"],
  rules: {
    // ── Vue-specific ─────────────────────────────────────────────
    "vue/multi-word-component-names": ["error", {
      ignores: ["default", "index", "Sidebar"],
    }],
    "vue/component-name-in-template-casing": ["error", "PascalCase"],
    "vue/html-self-closing": ["error", {
      html: { void: "never", normal: "always", component: "always" },
    }],
    "vue/require-default-prop": "warn",
    "vue/require-explicit-emits": "warn",

    // ── TypeScript ───────────────────────────────────────────────
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    "@typescript-eslint/explicit-function-return-type": "warn",

    // ── General ──────────────────────────────────────────────────
    "no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "error" : "off",

    // ── Brand: no hardcoded hex colors — use CSS variables ───────
    "no-restricted-syntax": [
      "error",
      {
        selector: "Literal[value=/^#[0-9a-fA-F]{3,8}$/]",
        message: "Do not hardcode hex colors — use a CSS variable (e.g. var(--color-brand-700))",
      },
    ],
  },
};
