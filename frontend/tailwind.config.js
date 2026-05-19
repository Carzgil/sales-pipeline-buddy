/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#faf8f4",
        surface: {
          DEFAULT: "#ffffff",
          2: "#f7f3ee",
        },
        edge: "#e3ddd5",
        ink: {
          DEFAULT: "#1a1714",
          dim: "#6b6560",
          faint: "#b0a89e",
        },
        flame: {
          DEFAULT: "#e87020",
          dim: "#fff5ee",
        },
        ember: {
          DEFAULT: "#1a7a45",
          dim: "#edf7f1",
        },
        sand: {
          DEFAULT: "#7a5c00",
          dim: "#fdf8e8",
        },
        ash: {
          DEFAULT: "#8b2020",
          dim: "#fdf0f0",
        },
        navy: "#1c2b3a",
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', "Georgia", "serif"],
        mono: ['"Azeret Mono"', '"Courier New"', "monospace"],
        sans: ["Outfit", "system-ui", "sans-serif"],
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "dot-pulse": {
          "0%, 100%": { opacity: "0.3", transform: "scale(0.75)" },
          "50%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.45s cubic-bezier(0.16, 1, 0.3, 1) both",
        "dot-pulse": "dot-pulse 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
