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
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#008a3d",
          800: "#00662b",
          900: "#14532d",
          950: "#052e16",
          soft: "rgba(0, 138, 61, 0.08)",
        },
        page: "#f9f7e8",
        surface: "#ffffff",
        muted: "#f4f2e4",
      },
      textColor: {
        primary: "#1a1a1a",
        secondary: "#5c5c5c",
        tertiary: "#757265",
      },
      borderColor: {
        default: "#e8e6d8",
        subtle: "#f0efe5",
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "12px",
      },
      boxShadow: {
        card: "none",
        elevated: "none",
        sidebar: "none",
      },
      transitionDuration: {
        DEFAULT: "150ms",
      },
    },
  },
};
