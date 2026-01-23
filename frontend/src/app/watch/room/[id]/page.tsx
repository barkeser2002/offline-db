import React from "react";
import { watchPartyService, contentService, authService } from "@/services/api";
import VideoPlayer from "@/components/watch/VideoPlayer";
import { notFound, redirect } from "next/navigation";

// Since this is a dynamic route and we might need headers/cookies
export const dynamic = "force-dynamic";

interface WatchPartyPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function WatchPartyPage({ params }: WatchPartyPageProps) {
  const { id } = await params;

  if (!id) {
    notFound();
  }

  try {
    // 1. Fetch Room Details
    const room = await watchPartyService.getRoom(id);

    if (!room || !room.is_active) {
      // Room closed or invalid
      return (
        <div className="min-h-screen flex items-center justify-center flex-col gap-4 text-center">
          <h1 className="text-2xl font-bold">Room not found or closed</h1>
          <p>This watch party has ended.</p>
        </div>
      );
    }

    // 2. Fetch Episode Details (to get video sources, etc.)
    // Note: Room serializer might include simple episode data, but we need full details (sources)
    // Checking if room.episode has full data depends on backend serializer.
    // Usually it's safer to fetch fresh detailed episode data.
    const episodeDetail = await contentService.getEpisodeDetail(room.episode.id.toString());

    // Fetch Anime Detail for context (total episodes etc.) if needed
    // Assuming episodeDetail has season -> anime -> id
    let animeId = "";
    if (episodeDetail.season?.anime?.id) {
      animeId = episodeDetail.season.anime.id.toString();
    }

    // 3. Get Current User (Mock or Server Session)
    // In a real Server Component, we'd get session from cookies/headers.
    // For now, VideoPlayer handles 'currentUser' somewhat, but useSyncManager
    // also relies on what it can get.
    // We will pass a placeholder or try to fetch profile if possible.
    // NOTE: 'authService.getProfile' relies on axios interceptors which work in browser or if we pass cookies manually.
    // Here we are on server. We can skip passing user and let client side fetch/determine user.

    return (
      <VideoPlayer
        episode={episodeDetail}
        animeId={animeId}
        roomUuid={room.uuid}
        // currentUser will be handled by client side logic or context
      />
    );

  } catch (error) {
    console.error("Error loading watch party:", error);
    return (
        <div className="min-h-screen flex items-center justify-center flex-col gap-4 text-center">
          <h1 className="text-2xl font-bold">Error loading party</h1>
          <p>Could not connect to the room.</p>
        </div>
      );
  }
}
