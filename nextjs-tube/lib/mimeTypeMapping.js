// lib/mimeTypeMapping.js

const supportedFormats = {
    'audio/mpeg': 'mp3',            // mp3 audio
    'audio/mp3': 'mp3',             // mp3 audio
    'audio/x-wav': 'wav',           // wav audio
    'audio/wav': 'wav',             // wav audio
    'audio/ogg': 'ogg',             // ogg audio
    'audio/x-flac': 'flac',         // flac audio
    'audio/flac': 'flac',           // flac audio
    'audio/mp4': 'mp4',             // mp4 audio
    'video/mp4': 'mp4',             // mp4 video
    'audio/webm': 'webm',           // webm audio
    'video/webm': 'webm',           // webm video
    'audio/m4a': 'm4a',             // m4a audio
    'audio/amr': 'amr',             // amr audio
    'audio/aac': 'aac',             // aac audio
    'audio/3gpp': '3gp',            // 3gp audio
    'video/3gpp': '3gp',            // 3gp video
    'audio/3gpp2': '3g2',           // 3g2 audio
    'video/3gpp2': '3g2',           // 3g2 video
    'application/octet-stream': 'bin', // binary files
  };
  
  const getMediaFormat = (mimeType) => {
    return supportedFormats[mimeType] || null;
  };
  
  export { getMediaFormat };
  