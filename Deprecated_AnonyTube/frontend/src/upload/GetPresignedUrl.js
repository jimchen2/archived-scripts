import Cookies from "js-cookie";
import { BACKEND_URL } from "../config";

export const getPresignedUrl = async (fileName) => {
  const token = Cookies.get("token");

  const presignedUrlResponse = await fetch(
    `${BACKEND_URL}/storage/presigned_url?file_name=${fileName}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!presignedUrlResponse.ok) {
    throw new Error("Failed to obtain presigned URL for video upload.");
  }

  const { presigned_url } = await presignedUrlResponse.json();
  return presigned_url;
};
