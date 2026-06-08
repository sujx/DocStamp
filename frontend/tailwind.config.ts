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
        card: "0 1px 2px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.05)",
        elevated: "0 4px 12px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04)",
        sidebar: "1px 0 4px rgba(0,0,0,0.04)",
      },
    },
  },
};
