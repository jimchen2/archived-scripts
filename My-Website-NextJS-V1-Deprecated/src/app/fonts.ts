import { Inter, Roboto, Open_Sans, Lato, Montserrat, Poppins, Nunito, Raleway } from 'next/font/google'

export const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

export const roboto = Roboto({ 
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  variable: '--font-roboto',
})

export const openSans = Open_Sans({ 
  subsets: ['latin'],
  variable: '--font-open-sans',
})

export const lato = Lato({ 
  weight: ['300', '400', '700'],
  subsets: ['latin'],
  variable: '--font-lato',
})

export const montserrat = Montserrat({ 
  subsets: ['latin'],
  variable: '--font-montserrat',
})

export const poppins = Poppins({ 
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  variable: '--font-poppins',
})

export const nunito = Nunito({ 
  subsets: ['latin'],
  variable: '--font-nunito',
})

export const raleway = Raleway({ 
  subsets: ['latin'],
  variable: '--font-raleway',
})
