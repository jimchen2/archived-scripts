// src/pages/blog/[id].js
import * as React from 'react';
import BlogDetail from '../../components/BlogPreview';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';

export default function BlogPage({ blog }) {
  if (!blog) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return <BlogDetail blog={blog} />;
}

export async function getServerSideProps({ params }) {
  const res = await fetch(`http://localhost:3000/api/blog/${params.id}`);
  const data = await res.json();

  if (!data.success) {
    return { notFound: true };
  }

  return {
    props: {
      blog: data.blog,
    },
  };
}