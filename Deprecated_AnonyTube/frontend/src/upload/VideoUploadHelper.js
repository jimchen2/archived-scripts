import { fetchUser } from "../FetchUser";
import { getPresignedUrl } from "./GetPresignedUrl";
import { postVideoDataToBackend, uploadFile } from "./UpdatePostgres";

export const VideoUploadHelper = async (
  selectedFile,
  selectedImage,
  onUploadProgress,
  onUploadComplete,
  onUploadError
) => {
  if (!selectedFile) {
    onUploadError("Please select a video file first!");
    return;
  }

  try {
    const user = await fetchUser();
    if (!user || !user.user_id) {
      onUploadError(
        "User ID could not be fetched. User might not be logged in."
      );
      return;
    }

    // Construct the structured format for video and image file names.
    const timestamp = Date.now().toString();

    const structuredVideoName = `${timestamp}|||${user.user_id}|||${selectedFile.name}`;
    const videoPresignedUrl = await getPresignedUrl(structuredVideoName);

    await uploadFile(
      videoPresignedUrl,
      selectedFile,
      "video/mp4",
      onUploadProgress
    );

    let structuredImageName;
    if (selectedImage) {
      structuredImageName = `${timestamp}|||${user.user_id}|||${selectedFile.name}.png`;
      const imagePresignedUrl = await getPresignedUrl(structuredImageName);
      await uploadFile(imagePresignedUrl, selectedImage, "image/png");
    }

    await postVideoDataToBackend({
      userId: user.user_id,
      videoTitle: structuredVideoName,
      videoUrl: videoPresignedUrl,
      imageUrl: structuredImageName ? structuredImageName : undefined,
    });

    onUploadComplete();
  } catch (error) {
    onUploadError(error.message);
  }
};
