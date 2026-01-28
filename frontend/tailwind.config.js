/** @type {import('tailwindcss').Config} */
import daisyui from "daisyui";
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    // v4 theme config is in CSS, but plugins like daisyui still read this for theme definitions
    plugins: [daisyui],
    daisyui: {
        themes: [
            {
                swiggyTheme: {
                    "primary": "#FF5200",
                    "secondary": "#2D1B69",
                    "accent": "#00C853",
                    "neutral": "#1f2937",
                    "base-100": "#ffffff",
                    "base-200": "#FFF8F3", // Light peach
                    "base-300": "#FFE5D9",
                    "info": "#3ABFF8",
                    "success": "#36D399",
                    "warning": "#FBBD23",
                    "error": "#F87272",
                },
                swiggyDark: {
                    "primary": "#FF5200",
                    "secondary": "#4A2C8F",
                    "accent": "#00C853",
                    "neutral": "#0A1929",
                    "base-100": "#0A1929", // Deep Navy
                    "base-200": "#06121E",
                    "base-300": "#02080D",
                    "info": "#3ABFF8",
                    "success": "#36D399",
                    "warning": "#FBBD23",
                    "error": "#FF6B6B",
                }
            },
            "light", "dark"
        ],
    },
}
