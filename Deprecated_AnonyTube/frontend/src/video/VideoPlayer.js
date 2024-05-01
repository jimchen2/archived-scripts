// VideoPlayerWithDownload.js

import React from 'react';
import { Player, ControlBar } from 'video-react';
import 'video-react/dist/video-react.css'; // Import video-react styles
import DownloadButton from './DownloadButton'; // Import your custom button

const VideoPlayerWithDownload = ({ src }) => {
  return (
    <Player
      src={src}
      autoPlay
    >
      <ControlBar autoHide={false} className="my-class">
        <DownloadButton order={7} />
      </ControlBar>
    </Player>
  );
};

export default VideoPlayerWithDownload;
