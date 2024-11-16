// src/app/api/posts/route.ts
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const lang = searchParams.get('lang');
  const posts = await prisma.post.findMany({
    where: { lang: lang as string },
    orderBy: { publishedAt: "desc" },
    select: {
      id: true,
      title: true,
      type: true,
      publishedAt: true
    }
  });
  return NextResponse.json(posts);
}
