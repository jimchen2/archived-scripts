"use client";

import React, { useEffect } from "react";
import { useParams } from "next/navigation";
import { redirect } from "next/navigation";

const BlogPage = () => {
  const params = useParams();

  redirect("/?blog=" + params.id);
};

export default BlogPage;