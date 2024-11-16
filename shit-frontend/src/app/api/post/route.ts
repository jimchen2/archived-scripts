// app/api/post/route.ts
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const lang = searchParams.get('lang');
  const type = searchParams.get('type');
  const title = searchParams.get('title');

  if (!lang || !type || !title) {
    return NextResponse.json({ error: 'Missing parameters' }, { status: 400 });
  }

  try {
    const post = await prisma.post.findFirst({
      where: {
        lang,
        type: decodeURIComponent(type),
        title: decodeURIComponent(title),
      },
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    return NextResponse.json(post);
  } catch (error) {
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}
