import React from "react";
import { ProgressBar, Container, Col, Button, Modal, Spinner } from "react-bootstrap";
import { useVideoUpload } from "./HandleUpload";
import { Link } from "react-router-dom";

const VideoUpload = () => {
  const {
    selectedFile,
    selectedImage,
    uploadProgress,
    totalSize,
    showModal,
    modalTitle,
    modalContent,
    isUploading,
    handleFileChange,
    handleImageChange,
    handleUploadClick,
    handleCloseModal,
  } = useVideoUpload();

  return (
    <Container
      className="d-flex justify-content-center"
      style={{ minHeight: "100vh" }}
    >
      <Col md={6}>
        <br />

        <h2 className="text-center mb-4">Upload Video</h2>

        <div className="mb-3">
          <label htmlFor="videoUpload" className="form-label">
            Select Video File
          </label>
          <input
            id="videoUpload"
            type="file"
            accept="video/*"
            className="form-control"
            onChange={handleFileChange}
            aria-label="Select video file"
          />
        </div>

        <div className="mb-3">
          <label htmlFor="imageUpload" className="form-label">
            Select Preview Image
          </label>
          <input
            id="imageUpload"
            type="file"
            accept="image/*"
            className="form-control"
            onChange={handleImageChange}
            aria-label="Select preview image"
          />
        </div>

        <div className="d-grid mb-3">
          <Button
            variant="primary"
            size="lg"
            onClick={handleUploadClick}
            disabled={isUploading || !selectedFile || !selectedImage}
          >
            {isUploading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Uploading...
              </>
            ) : (
              "Upload Video"
            )}
          </Button>
        </div>

        {selectedFile && (
          <div>
            <ProgressBar
              now={uploadProgress}
              label={`${uploadProgress.toFixed(2)}%`}
            />
            <p className="text-center mb-0">Total Size: {totalSize}</p>
          </div>
        )}

        <Modal show={showModal} onHide={handleCloseModal} centered>
          <Modal.Header closeButton>
            <Modal.Title>{modalTitle}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <p>{modalContent}</p>
            {modalTitle === "Success" ? (
              <div className="d-grid">
                <Link to="/" className="btn btn-primary btn-block">
                  Go Home
                </Link>
              </div>
            ) : (
              <div className="d-grid">
                <Button variant="secondary" onClick={handleCloseModal}>
                  Close
                </Button>
              </div>
            )}
          </Modal.Body>
        </Modal>
      </Col>
    </Container>
  );
};

export default VideoUpload;