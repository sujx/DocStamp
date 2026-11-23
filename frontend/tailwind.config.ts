import type { Config } from "tailwindcss";

export default <Config>{
  content: [
    "./components/**/*.{vue,js,ts}",
    "./pages/**/*.{vue,js,ts}",
    "./layouts/**/*.{vue,js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EFF4FE",
          100: "#DDE8FD",
          200: "#BCD0FA",
          300: "#93B4F6",
          400: "#6E95F2",
          500: "#4C7DF0",
          600: "#3B63D8",
          700: "#2F4FB0",
          800: "#27408D",
          900: "#1F3268",
          950: "#14213D",
          soft: "rgba(76, 125, 240, 0.10)",
        },
        seal: "#C0392B",
        page: "#EEF0F4",
        surface: "#ffffff",
        muted: "#F4F6FA",
        raised: "#ECEFF4",
        sidebar: "#23337A",
      },
      textColor: {
        primary: "#1F2A44",
        secondary: "#56627A",
        tertiary: "#6E7A93",
      },
      borderColor: {
        default: "rgba(31, 42, 68, 0.10)",
        subtle: "rgba(31, 42, 68, 0.06)",
        strong: "rgba(31, 42, 68, 0.18)",
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        full: "9999px",
      },
      boxShadow: {
        xs: "0 1px 2px rgba(16, 24, 40, 0.05)",
        card: "0 1px 2px rgba(16, 24, 40, 0.05)",
        elevated: "0 8px 24px rgba(16, 24, 40, 0.06)",
        sidebar: "0 8px 24px rgba(16, 24, 40, 0.08)",
        subtle: "0 1px 2px rgba(16, 24, 40, 0.05)",
      },
      transitionDuration: {
        DEFAULT: "160ms",
      },
      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
      animation: {
        "fade-up": "fade-up 400ms cubic-bezier(0.22, 1, 0.36, 1) both",
      },
    },
  },
};
