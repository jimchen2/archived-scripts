import React from "react";
import Navbar from "./navbar/navbar";
import "./globals.css";
import { inter, roboto, openSans, lato, montserrat, poppins, nunito, raleway } from './fonts'

export const metadata = {
  title: "Jim Chen's Website",
  description: "Jim Chen's personal website",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${roboto.variable} ${openSans.variable} ${lato.variable} ${montserrat.variable} ${poppins.variable} ${nunito.variable} ${raleway.variable}`}>
      <body className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow">{children}</main>
      </body>
    </html>
  );
}