"use client";

import { useEffect, useRef } from "react";

/**
 * V-02: HLS (adaptive bitrate) pleyer. V-07: PiP/klaviatura/to'liq ekran —
 * <video> native controls orqali brauzer ta'minlaydi.
 */
export default function VideoPlayer({ manifestUrl, watermarkText, onProgress }) {
  const videoRef = useRef(null);

  useEffect(() => {
    if (!manifestUrl || !videoRef.current) return;
    let hls;
    const video = videoRef.current;

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = manifestUrl; // Safari — native HLS
    } else {
      import("hls.js").then(({ default: Hls }) => {
        if (Hls.isSupported()) {
          hls = new Hls();
          hls.loadSource(manifestUrl);
          hls.attachMedia(video);
        }
      });
    }
    return () => hls?.destroy();
  }, [manifestUrl]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !onProgress) return;
    const interval = setInterval(() => {
      if (!video.paused) {
        onProgress({ position: Math.floor(video.currentTime), watched: Math.floor(video.currentTime) });
      }
    }, 60000); // 5.7: har 60 sekundda flush
    return () => clearInterval(interval);
  }, [onProgress]);

  return (
    <div style={{ position: "relative" }}>
      <video ref={videoRef} controls style={{ width: "100%", borderRadius: 10 }} />
      {watermarkText && (
        <div
          style={{
            position: "absolute", bottom: 10, right: 14, color: "rgba(255,255,255,0.6)",
            fontSize: 12, pointerEvents: "none", textShadow: "0 0 3px rgba(0,0,0,0.8)",
          }}
        >
          {watermarkText}
        </div>
      )}
    </div>
  );
}
