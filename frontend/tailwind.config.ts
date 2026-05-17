import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        portal: {
          50:  "#f0f4ff",
          100: "#dce6ff",
          200: "#baccff",
          300: "#87a9ff",
          400: "#517bff",
          500: "#2d52ff",
          600: "#1630f5",
          700: "#1225e1",
          800: "#1520b6",
          900: "#16208f",
          950: "#101456",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
