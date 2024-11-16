// src/app/[lang]/[type]/[title]/page.tsx
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

async function getPost(lang: string, type: string, title: string) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
  
  const response = await fetch(
    `${baseUrl}/api/post?lang=${lang}&type=${encodeURIComponent(type)}&title=${encodeURIComponent(title)}`,
    {
      cache: 'no-store',
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch post');
  }

  return response.json();
}

export default async function PostPage({ params }: { params: { lang: string; type: string; title: string } }) {
  const { lang, type, title } = await params;
  
  try {
    const post = await getPost(lang, type, title);

    return (
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <div className="text-2xl font-bold">{post.title.replaceAll("-", " ")}</div>
        <div>
          type: {post.type}
          <br />
          date: {new Date(post.publishedAt).toLocaleDateString()}
        </div>
        <MarkdownRenderer content={post.text} />
      </div>
    );
  } catch (error) {
    return <div>Post not found</div>;
  }
}
