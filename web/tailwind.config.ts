import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f5f3ff",
        surface: "#ffffff",
        card: "#ffffff",
        border: "#ede9fe",
        "text-primary": "#1e1b4b",
        "text-secondary": "#6b7280",
        accent: "#7c3aed",
        "accent-light": "#ede9fe",
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        "type-appointment": "#7c3aed",
        "type-scan": "#ec4899",
        "type-vet": "#10b981",
        "type-birthday": "#f59e0b",
        "type-other": "#6b7280",
      },
      fontFamily: {
        sans: ["system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
