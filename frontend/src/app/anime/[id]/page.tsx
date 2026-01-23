import { contentService } from "@/services/api";
import {
  Button,
  Chip,
  Card,
  CardBody,
  Image as NextUIImage,
  Tabs,
  Tab,
} from "@nextui-org/react";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function AnimeDetail({
  params,
}: {
  params: { id: string };
}) {
  let anime;
  try {
    anime = await contentService.getAnimeDetail(params.id);
  } catch (error) {
    notFound();
  }

  return (
    <main className="min-h-screen pb-20">
      {/* Banner */}
      <div className="relative h-[40vh] min-h-[400px]">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(${anime.banner_image || anime.cover_image})`,
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/90 to-transparent" />

        {/* Content */}
        <div className="absolute inset-0 flex items-end">
          <div className="max-w-7xl mx-auto px-4 w-full flex flex-col md:flex-row gap-8 pb-8">
            {/* Poster */}
            <div className="flex-shrink-0 mx-auto md:mx-0">
              <Card className="w-[220px] h-[330px] border border-white/10 shadow-2xl">
                <NextUIImage
                  src={anime.cover_image}
                  alt={anime.title}
                  classNames={{
                    img: "w-full h-full object-cover",
                    wrapper: "w-full h-full",
                  }} // Fixing Image styling in NextUI
                />
              </Card>
            </div>

            {/* Info */}
            <div className="flex-1 text-center md:text-left">
              <h1 className="text-4xl font-bold text-foreground mb-4">
                {anime.title}
              </h1>
              <div className="flex flex-wrap justify-center md:justify-start gap-4 mb-6">
                <div className="flex items-center gap-1">
                  <span className="text-yellow-400 text-xl">★</span>
                  <span className="text-xl font-bold">
                    {anime.score || "N/A"}
                  </span>
                </div>
                <div className="w-px h-6 bg-white/20" />
                <span>{anime.type}</span>
                <div className="w-px h-6 bg-white/20" />
                <span>{anime.status}</span>
                <div className="w-px h-6 bg-white/20" />
                <span>{anime.studio}</span>
              </div>

              <div className="flex justify-center md:justify-start gap-4">
                <Button
                  color="primary"
                  size="lg"
                  className="font-bold px-8"
                  // Link to first episode if available
                  isDisabled={!anime.seasons?.[0]?.episodes?.[0]?.id}
                  as={Link}
                  href={`/watch/${anime.id}/${anime.seasons?.[0]?.episodes?.[0]?.id || ""}`}
                >
                  Watch Now
                </Button>
                <Button variant="bordered" size="lg">
                  Add to List
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Synopsis */}
          <section>
            <h2 className="text-2xl font-bold mb-4">Synopsis</h2>
            <p className="text-foreground/80 leading-relaxed text-lg">
              {anime.synopsis}
            </p>
          </section>

          {/* Episodes */}
          <section>
            <h2 className="text-2xl font-bold mb-4">Episodes</h2>
            {anime.seasons && anime.seasons.length > 0 ? (
              <div className="space-y-4">
                {anime.seasons.map((season) => (
                  <div key={season.id}>
                    <h3 className="text-xl font-semibold mb-2">
                      {season.name || `Season ${season.number}`}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {season.episodes.map((ep) => (
                        <Link key={ep.id} href={`/watch/${anime.id}/${ep.id}`}>
                          <Card
                            isHoverable
                            isPressable
                            className="bg-surface border border-white/5 hover:border-primary/50"
                          >
                            <CardBody className="flex flex-row gap-4 p-3">
                              <div className="w-24 aspect-video bg-black/50 rounded flex-shrink-0 overflow-hidden">
                                {ep.cover_image ? (
                                  <img
                                    src={ep.cover_image}
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center text-xs text-white/30">
                                    No Image
                                  </div>
                                )}
                              </div>
                              <div>
                                <p className="font-semibold text-sm line-clamp-1">
                                  Ep {ep.number} - {ep.title}
                                </p>
                                <p className="text-xs text-foreground/50">
                                  {ep.duration} min
                                </p>
                              </div>
                            </CardBody>
                          </Card>
                        </Link>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-foreground/50">No episodes available.</p>
            )}
          </section>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Info Card */}
          <Card className="bg-surface border border-white/5">
            <CardBody className="space-y-4">
              <div>
                <span className="text-foreground/50 text-sm block">
                  Japanese
                </span>
                <span>{anime.japanese_title}</span>
              </div>
              <div>
                <span className="text-foreground/50 text-sm block">Aired</span>
                <span>{anime.aired_from}</span>
              </div>
              <div>
                <span className="text-foreground/50 text-sm block">Rank</span>
                <span>#{anime.rank}</span>
              </div>
              <div>
                <span className="text-foreground/50 text-sm block">
                  Popularity
                </span>
                <span>#{anime.popularity}</span>
              </div>
            </CardBody>
          </Card>

          {/* Genres */}
          <div>
            <h3 className="font-semibold mb-3">Genres</h3>
            <div className="flex flex-wrap gap-2">
              {anime.genres.map((genre) => (
                <Chip key={genre.id} variant="flat" size="sm">
                  {genre.name}
                </Chip>
              ))}
            </div>
          </div>

          {/* Characters */}
          <div>
            <h3 className="font-semibold mb-3">Characters</h3>
            <div className="grid grid-cols-2 gap-3">
              {anime.characters?.slice(0, 6).map((char) => (
                <div key={char.id} className="flex items-center gap-2">
                  <Avatar src={char.character.image_url} size="md" />{" "}
                  {/* Assuming Avatar component available/imported or use img */}
                  <div className="overflow-hidden">
                    <p className="text-sm font-medium truncate">
                      {char.character.name}
                    </p>
                    <p className="text-xs text-foreground/50">{char.role}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

// Helper needed because I used Avatar above without import
function Avatar({ src, size }: { src: string; size?: string }) {
  return (
    <div
      className={`rounded-full overflow-hidden bg-white/10 flex-shrink-0 ${size === "md" ? "w-10 h-10" : "w-8 h-8"}`}
    >
      {src ? <img src={src} className="w-full h-full object-cover" /> : null}
    </div>
  );
}
