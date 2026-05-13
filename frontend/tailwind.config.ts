import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        focus: {
          peak: "#6EE7B7",
          high: "#34D399",
          medium: "#FCD34D",
          low: "#F97316",
          minimal: "#EF4444",
          break: "#93C5FD",
          away: "#4B5563",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px currentColor" },
          "100%": { boxShadow: "0 0 20px currentColor, 0 0 40px currentColor" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
