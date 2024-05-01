// ./HandleUpload.js
import { useState } from "react";
import { VideoUploadHelper } from "./VideoUploadHelper";
import { useNavigate } from "react-router-dom";

export const useVideoUpload = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSize, setUploadSize] = useState("");
  const [totalSize, setTotalSize] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalContent, setModalContent] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setTotalSize(formatBytes(file.size));
    }
  };

  const handleImageChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
    }
  };

  const handleUploadProgress = (progress, event) => {
    setUploadProgress(progress);
    if (event) {
      setUploadSize(formatBytes(event.loaded));
      setTotalSize(formatBytes(event.total));
    }
  };

  const handleUploadComplete = () => {
    setModalTitle("Success");
    setModalContent("Video upload complete!");
    setShowModal(true);
    setIsUploading(false);
    setUploadProgress(0);
    setUploadSize("");
    setTotalSize("");
  };

  const handleUploadError = (error) => {
    setModalTitle("Error");
    setModalContent(error);
    setShowModal(true);
    setIsUploading(false);
    setUploadProgress(0);
    setUploadSize("");
    setTotalSize("");
  };

  const handleUploadClick = async () => {
    if (selectedFile && selectedImage && !isUploading) {
      setIsUploading(true);
      try {
        await VideoUploadHelper(
          selectedFile,
          selectedImage,
          handleUploadProgress,
          handleUploadComplete,
          handleUploadError
        );
      } catch (error) {
        console.error("Error setting up the upload:", error);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    navigate("/");
  };

  return {
    selectedFile,
    selectedImage,
    uploadProgress,
    uploadSize,
    totalSize,
    showModal,
    modalTitle,
    modalContent,
    isUploading,
    handleFileChange,
    handleImageChange,
    handleUploadClick,
    handleCloseModal,
  };
};