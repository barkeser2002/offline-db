import { contentService } from "@/services/api";
import VideoPlayer from "@/components/watch/VideoPlayer";
import { notFound } from "next/navigation";

interface WatchPageProps {
  params: {
    slug: string[];
  };
}

export default async function WatchPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string[] }>;
  searchParams: Promise<{ room?: string }>;
}) {
  const resolvedParams = await params;
  const resolvedSearchParams = await searchParams;

  const [animeId, episodeId] = resolvedParams.slug;
  const { room } = resolvedSearchParams;

  if (!animeId || !episodeId) {
    notFound();
  }

  let episodeDetail;
  let animeDetail;

  try {
    episodeDetail = await contentService.getEpisodeDetail(episodeId);
    animeDetail = await contentService.getAnimeDetail(animeId);
  } catch (error) {
    console.error("Error fetching watch data", error);
    notFound();
  }

  // TODO: Fetch current user from session if available
  // const currentUser = await authService.getCurrentUser();
  // For now, VideoPlayer will assume anonymous or handle it if we pass it.
  // Actually, useSyncManager handles connection, backend handles auth via Token/Session.

  return (
    <VideoPlayer
      episode={episodeDetail}
      animeId={animeId}
      totalEpisodes={(animeDetail as any).total_episodes || 12}
      roomUuid={room}
      currentUser={{ id: 1, username: "Guest" }} // Placeholder until Auth integration
    />
  );
}
