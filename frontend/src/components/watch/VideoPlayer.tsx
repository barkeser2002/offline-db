"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Button,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  Switch,
  Slider,
} from "@nextui-org/react";
import Link from "next/link";
import { EpisodeDetail } from "@/services/api";
import { WebGLRenderer } from "../player/Anime4K/WebGLRenderer";
import { useSyncManager } from "../watchparty/useSyncManager";
import { PartyPanel } from "../watchparty/PartyPanel";

interface VideoPlayerProps {
  episode: EpisodeDetail;
  animeId: string;
  totalEpisodes?: number;
  roomUuid?: string; // WatchParty Room ID
  currentUser?: { id: number; username: string }; // Provided by parent
}

export default function VideoPlayer({
  episode,
  animeId,
  totalEpisodes = 12,
  roomUuid,
  currentUser,
}: VideoPlayerProps) {
  const directSources = episode.video_files || [];
  const externalSources = episode.external_sources || [];

  // Player State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [selectedQuality, setSelectedQuality] = useState(
    directSources[0]?.quality || "1080p",
  );

  // Anime4K State
  const [anime4kEnabled, setAnime4kEnabled] = useState(false);

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<HTMLDivElement>(null);
  const controlsTimeout = useRef<NodeJS.Timeout | undefined>(undefined);

  // Sync volume/muted with video element
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.volume = volume;
      videoRef.current.muted = isMuted;
    }
  }, [volume, isMuted]);

  // WatchParty Sync logic
  const {
    isConnected,
    chatMessages,
    participants,
    sendSync,
    sendMessage,
    sendEmote,
  } = useSyncManager(roomUuid || "", currentUser, videoRef);

  // Determine Source
  const currentSourceUrl =
    directSources.find((s) => s.quality === selectedQuality)?.file_url ||
    externalSources[0]?.url ||
    ""; // Fallback

  // Intro Skip Logic
  const [showIntroSkip, setShowIntroSkip] = useState(false);

  // Event Listeners
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime;
      setCurrentTime(time);
      if (time >= 80 && time <= 120) setShowIntroSkip(true);
      else setShowIntroSkip(false);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handlePlay = () => {
    setIsPlaying(true);
    if (roomUuid) sendSync("playing", videoRef.current?.currentTime || 0);
  };

  const handlePause = () => {
    setIsPlaying(false);
    if (roomUuid) sendSync("paused", videoRef.current?.currentTime || 0);
  };

  const handleSeek = (e: any) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
      if (roomUuid) sendSync(isPlaying ? "playing" : "paused", time);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      playerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeout.current) clearTimeout(controlsTimeout.current);
    controlsTimeout.current = setTimeout(() => {
      if (isPlaying) setShowControls(false);
    }, 3000);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Emote Rain Effect (Simple DOM overlay)
  const [emotes, setEmotes] = useState<
    { id: number; char: string; left: number }[]
  >([]);
  useEffect(() => {
    const handleEmote = (e: any) => {
      const char = e.detail.emote;
      const id = Date.now();
      setEmotes((prev) => [
        ...prev,
        { id, char, left: Math.random() * 90 + 5 },
      ]);
      setTimeout(() => {
        setEmotes((prev) => prev.filter((item) => item.id !== id));
      }, 3000);
    };
    window.addEventListener("emote-rain", handleEmote);
    return () => window.removeEventListener("emote-rain", handleEmote);
  }, []);

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-black">
      {/* Video Area */}
      <div className="flex-1 flex flex-col relative items-center justify-center bg-black">
        <div
          ref={playerRef}
          className="relative w-full h-full bg-black group"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => isPlaying && setShowControls(false)}
        >
          {/* Main Video */}
          <video
            ref={videoRef}
            src={currentSourceUrl}
            className="w-full h-full object-contain"
            onClick={() =>
              isPlaying ? videoRef.current?.pause() : videoRef.current?.play()
            }
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={handlePlay}
            onPause={handlePause}
          />

          {/* WebGL Overlay (Anime4K) */}
          {anime4kEnabled && (
            <WebGLRenderer videoRef={videoRef} width={1920} height={1080} />
          )}

          {/* Emote Rain Layer */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden z-30">
            {emotes.map((emote) => (
              <motion.div
                key={emote.id}
                initial={{ y: -50, opacity: 1 }}
                animate={{ y: 800, opacity: 0 }}
                transition={{ duration: 2, ease: "linear" }}
                className="absolute text-4xl"
                style={{ left: `${emote.left}%` }}
              >
                {emote.char}
              </motion.div>
            ))}
          </div>

          {/* Intro Skip */}
          {showIntroSkip && (
            <motion.div
              initial={{ x: 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              className="absolute bottom-24 right-8 z-50 pointer-events-auto"
            >
              <Button
                size="sm"
                className="bg-white/10 backdrop-blur-md text-white border border-white/20"
                onClick={() => {
                  if (videoRef.current) videoRef.current.currentTime += 85;
                }}
              >
                Skip Intro
              </Button>
            </motion.div>
          )}

          {/* Controls UI */}
          <motion.div
            animate={{ opacity: showControls ? 1 : 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 z-40 bg-gradient-to-t from-black/80 via-transparent to-black/40 pointer-events-none flex flex-col justify-between"
          >
            {/* Top Bar */}
            <div className="p-4 flex justify-between items-center pointer-events-auto">
              <div className="text-white drop-shadow-md">
                <h2 className="font-bold text-lg">
                  {episode.title || `Episode ${episode.number}`}
                </h2>
              </div>
              <div className="flex gap-2">
                <div className="flex items-center gap-2 bg-black/40 px-3 py-1 rounded-full backdrop-blur-md border border-white/10">
                  <span className="text-xs font-bold text-pink-400">
                    Anime4K
                  </span>
                  <Switch
                    size="sm"
                    color="secondary"
                    isSelected={anime4kEnabled}
                    onValueChange={setAnime4kEnabled}
                  />
                </div>
              </div>
            </div>

            {/* Bottom Bar */}
            <div className="p-4 space-y-2 pointer-events-auto pb-8">
              {/* Timeline */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-white/70 w-10 text-right">
                  {formatTime(currentTime)}
                </span>
                <input
                  type="range"
                  min="0"
                  max={duration || 100}
                  value={currentTime}
                  onChange={handleSeek}
                  className="flex-1 h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <span className="text-xs text-white/70 w-10">
                  {formatTime(duration)}
                </span>
              </div>

              {/* Buttons */}
              <div className="flex justify-between items-center">
                <div className="flex gap-2 items-center">
                  <Button
                    isIconOnly
                    variant="light"
                    className="text-white"
                    onClick={() =>
                      isPlaying
                        ? videoRef.current?.pause()
                        : videoRef.current?.play()
                    }
                  >
                    {isPlaying ? "⏸" : "▶"}
                  </Button>
                  <Button
                    isIconOnly
                    variant="light"
                    className="text-white"
                    onClick={() => setIsMuted(!isMuted)}
                  >
                    {isMuted ? "🔇" : "🔊"}
                  </Button>
                </div>
                <div className="flex gap-2 items-center">
                  <Dropdown>
                    <DropdownTrigger>
                      <Button variant="light" size="sm" className="text-white">
                        {selectedQuality}
                      </Button>
                    </DropdownTrigger>
                    <DropdownMenu
                      onAction={(k) => setSelectedQuality(k as string)}
                    >
                      {directSources.map((s) => (
                        <DropdownItem key={s.quality}>{s.quality}</DropdownItem>
                      ))}
                    </DropdownMenu>
                  </Dropdown>
                  <Button
                    isIconOnly
                    variant="light"
                    className="text-white"
                    onClick={toggleFullscreen}
                  >
                    ⛶
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* WatchParty Sidebar (if active) */}
      {roomUuid && (
        <div className="w-80 h-full border-l border-divider bg-background z-50">
          <PartyPanel
            chatMessages={chatMessages}
            participants={participants}
            onSendMessage={sendMessage}
            onSendEmote={sendEmote}
            isConnected={isConnected}
          />
        </div>
      )}
    </div>
  );
}
