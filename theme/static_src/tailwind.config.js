/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,js,py}",
    "../../../templates/**/*.html",
    "../../../**/*.py",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        light: {
          ...require("daisyui/src/colors/themes")['[data-theme=light]'],
          "primary": "#2563eb",
          "primary-content": "#fff",
          "secondary": "#fbbf24",
          "accent": "#10b981",
          "neutral": "#18181b",
          "base-100": "#f9fafb",
          "base-200": "#f3f4f6",
          "base-300": "#e5e7eb",
          "info": "#0ea5e9",
          "success": "#22c55e",
          "warning": "#f59e42",
          "error": "#ef4444",
        },
      },
      "dark",
    ],
  },
};
