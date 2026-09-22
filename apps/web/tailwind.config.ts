import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07111f",
          900: "#0b1728",
          850: "#101e31",
          800: "#17263a",
          700: "#22354d",
        },
        signal: {
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(45,212,191,.12), 0 18px 50px rgba(0,0,0,.25)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(148,163,184,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.035) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

export default config;
