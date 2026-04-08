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
          50: "#f0f4ff",
          100: "#e0e8ff",
          500: "#3b5bdb",
          600: "#2f4ac4",
          700: "#2441ab",
          900: "#0d1f6b",
        },
      },
    },
  },
  plugins: [],
};

export default config;
