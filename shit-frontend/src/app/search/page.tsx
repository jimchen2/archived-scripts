"use client";

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const router = useRouter()
  const { locale } = router

  const handleSearch = async () => {
    if (!query.trim()) return

    try {
      const response = await fetch(
        `/api/search?q=${encodeURIComponent(query)}&lang=${locale || 'en'}`
      )
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Search failed:', error)
    }
  }

  const placeholders = {
    en: "Search...",
    zh: "搜索...",
    ru: "Поиск..."
  }

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholders[locale as keyof typeof placeholders] || placeholders.en}
      />
      <button onClick={handleSearch}>Search</button>

      <div>
        {results.map((post: any) => (
          <div key={post.id}>
            <h3>{post.title}</h3>
            <p>{post.text.substring(0, 200)}...</p>
          </div>
        ))}
      </div>
    </div>
  )
}
