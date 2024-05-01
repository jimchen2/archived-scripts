import Cookies from "js-cookie";
import { BACKEND_URL } from "../config";

export const postVideoDataToBackend = async (data) => {
  const { userId, videoTitle, videoUrl, imageUrl } = data;
  const token = Cookies.get("token");
  try {
    const response = await fetch(
      `${BACKEND_URL}/user-videos/${userId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: videoTitle,
          videoUrl,
          imageUrl,
        }),
      }
    );
  
    if (!response.ok) {
      throw new Error('Failed to save video metadata.');
    }
  
    return await response.json(); // this return can be used if needed
  } catch (error) {
    throw error; // Let the caller handle the error
  }
};

export const uploadFile = async (presignedUrl, file, contentType, onProgress) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', presignedUrl);
  
    if (onProgress && xhr.upload) {
      xhr.upload.onprogress = function(event) {
        if (event.lengthComputable) {
          const percentage = (event.loaded / event.total) * 100;
          onProgress(percentage);
        }
      };
    }
  
    xhr.onload = function() {
      if (this.status === 200) {
        resolve();
      } else {
        reject(new Error(`Upload failed: ${this.status}`));
      }
    };
  
    xhr.onerror = function() {
      reject(new Error('Upload error.'));
    };
  
    xhr.setRequestHeader('Content-Type', contentType);
    xhr.send(file);
  });
};
