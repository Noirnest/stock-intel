/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'JetBrains Mono'", "monospace"],
        display: ["'IBM Plex Sans'", "sans-serif"],
      },
      colors: {
        // Terminal dark palette
        surface: {
          DEFAULT: "#0a0a0f",
          1: "#111118",
          2: "#1a1a24",
          3: "#222230",
        },
        border: {
          DEFAULT: "#2a2a3a",
          subtle: "#1e1e2a",
        },
        accent: {
          green:  "#00ff88",
          red:    "#ff4444",
          amber:  "#ffaa00",
          blue:   "#4488ff",
          purple: "#aa66ff",
          cyan:   "#00ddff",
        },
        text: {
          primary:   "#e8e8f0",
          secondary: "#8888aa",
          muted:     "#555568",
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-in": "slideIn 0.2s ease-out",
        "fade-in": "fadeIn 0.3s ease-out",
        "flash": "flash 0.5s ease-out",
      },
      keyframes: {
        slideIn: {
          "0%": { transform: "translateY(-4px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        flash: {
          "0%": { backgroundColor: "rgba(0,255,136,0.15)" },
          "100%": { backgroundColor: "transparent" },
        },
      },
    },
  },
  plugins: [],
};
