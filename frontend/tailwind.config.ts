import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design tokens de ANDROMEDA
        andromeda: {
          50:  "#f0f4ff",
          100: "#e0e8ff",
          400: "#8b9fee",
          500: "#667eea",
          600: "#5a6fd6",
          700: "#4a5bc4",
          800: "#3a4ab2",
          900: "#1a1a3e",
        },
        galaxy: {
          bg:      "#0a0a1a",
          surface: "rgba(255,255,255,0.04)",
          border:  "rgba(255,255,255,0.08)",
          purple:  "#764ba2",
          accent:  "#f64f59",
        },
      },
    },
  },
  plugins: [],
};

export default config;
