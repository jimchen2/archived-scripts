// src/app/[lang]/page.tsx
import Link from "next/link";

export default async function LangPage({ params }: { params: { lang: string } }) {
  const posts = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'}/api/metadata?lang=${params.lang}`).then(res => res.json());

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
      {posts.map((post) => (
        <div key={post.id} className="flex gap-4">
          <span className="w-24 shrink-0">{new Date(post.publishedAt).toLocaleDateString()}</span>
          <Link href={`/${params.lang}/${post.type}/${post.title}`}>
            <span className="underline">{post.title.replaceAll('-', ' ')}</span>
          </Link>
        </div>
      ))}
    </div>
  );
}
