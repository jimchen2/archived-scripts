// src/app/api/search/route.ts
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { Prisma } from "@prisma/client";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("q");
    const lang = searchParams.get("lang") || "en";

    if (!query) {
      return NextResponse.json(
        {
          success: false,
          error: "Query parameter is required",
        },
        { status: 400 }
      );
    }

    // Convert language code to PostgreSQL language name
    const languageMap: { [key: string]: string } = {
      en: "english",
      cn: "simple",
      ru: "russian",
    };

    const searchLanguage = languageMap[lang] || "english";

    const posts = await prisma.$queryRaw`
      SELECT title, lang
      FROM posts 
      WHERE lang = ${lang} 
      AND search_vector @@ plainto_tsquery(${searchLanguage}::regconfig, ${query})
      LIMIT 5
    `;

    return NextResponse.json({
      success: true,
      data: posts,
    });
  } catch (error) {
    console.error("Search error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Search failed",
      },
      { status: 500 }
    );
  }
}
