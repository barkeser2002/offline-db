import { contentService } from "@/services/api";
import HeroSection from "@/components/home/HeroSection";
import TrendingSection from "@/components/home/TrendingSection";
import CommunityLive from "@/components/home/CommunityLive";
import StatsSection from "@/components/home/StatsSection";

// Force dynamic rendering since data changes frequently
export const dynamic = "force-dynamic";

export default async function Home() {
  let homeData = {
    trending: [],
    latest_episodes: [],
    seasonal: [],
  };

  try {
    homeData = await contentService.getHomeData();
  } catch (error) {
    console.error("Failed to fetch home data:", error);
    // In a real scenario, we might show an error state or cached data
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Hero Section - Using Trending for slider */}
      <HeroSection slides={homeData.trending.slice(0, 5)} />

      {/* Trending Section */}
      <TrendingSection items={homeData.trending} />

      {/* Stats - Static for now */}
      <StatsSection />

      {/* Community */}
      <CommunityLive />
    </main>
  );
}
