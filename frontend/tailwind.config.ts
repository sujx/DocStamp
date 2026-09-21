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
        sidebar: "#23337A",
      },
      textColor: {
        primary: "#1F2A44",
        secondary: "#56627A",
        tertiary: "#6E7A93",
      },
      borderColor: {
        default: "#E3E8F0",
        subtle: "#EEF0F4",
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        full: "9999px",
      },
      boxShadow: {
        xs: "0 1px 2px rgba(26, 43, 79, 0.04)",
        card: "0 2px 6px rgba(26, 43, 79, 0.05), 0 1px 2px rgba(26, 43, 79, 0.04)",
        elevated: "0 6px 14px -2px rgba(26, 43, 79, 0.07), 0 2px 6px -2px rgba(26, 43, 79, 0.04)",
        sidebar: "0 12px 22px -4px rgba(26, 43, 79, 0.08), 0 6px 10px -4px rgba(26, 43, 79, 0.04)",
        subtle: "0 1px 2px rgba(26, 43, 79, 0.04)",
      },
      transitionDuration: {
        DEFAULT: "200ms",
      },
      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(.16, 1, .3, 1)",
        spring: "cubic-bezier(.16, 1, .3, 1)",
      },
      animation: {
        "fade-up": "fade-up 0.4s cubic-bezier(.16, 1, .3, 1) both",
      },
    },
  },
};
