import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        kept: "var(--color-kept)",
        moved: "var(--color-moved)",
        broken: "var(--color-broken)",
      },
    },
  },
  plugins: [],
} satisfies Config;