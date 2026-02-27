import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        surface: "var(--surface)",
        card: "var(--surface)",
        border: "var(--border)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        accent: "#7c3aed",
        "accent-light": "var(--accent-light)",
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
