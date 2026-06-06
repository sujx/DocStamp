module.exports = {
  root: true,
  extends: ["@nuxtjs/eslint-config-typescript"],
  rules: {
    "vue/multi-word-component-names": "off",
    "no-console": "warn",
    // Brand: no hardcoded hex colors — use CSS variables
    "no-restricted-syntax": [
      "error",
      {
        selector: "Literal[value=/^#[0-9a-fA-F]{3,8}$/]",
        message: "Do not hardcode hex colors — use a CSS variable (e.g. var(--color-brand-700))",
      },
    ],
  },
};
