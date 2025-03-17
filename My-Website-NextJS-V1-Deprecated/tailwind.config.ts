import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/pages/**/*.{js,ts,jsx,tsx,mdx}", "./src/components/**/*.{js,ts,jsx,tsx,mdx}", "./src/app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        inter: ['var(--font-inter)'],
        roboto: ['var(--font-roboto)'],
        opensans: ['var(--font-open-sans)'],
        lato: ['var(--font-lato)'],
        montserrat: ['var(--font-montserrat)'],
        poppins: ['var(--font-poppins)'],
        nunito: ['var(--font-nunito)'],
        raleway: ['var(--font-raleway)'],
        kalam: ["Kalam", "cursive"],
        caveat: ["Caveat", "cursive"],
        indieFlower: ["Indie Flower", "cursive"],
        quicksand: ["Quicksand", "sans-serif"],
        comicsans: ["Comic Sans MS", "cursive"],
      },
    },
  },
  plugins: [],
};

export default config;
