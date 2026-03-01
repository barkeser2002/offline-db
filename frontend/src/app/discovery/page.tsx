"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Input,
  Button,
  Card,
  CardBody,
  Chip,
  Select,
  SelectItem,
  Slider,
} from "@nextui-org/react";
import Link from "next/link";

// Sample data
const genres = [
  "Action",
  "Adventure",
  "Comedy",
  "Drama",
  "Fantasy",
  "Horror",
  "Mystery",
  "Romance",
  "Sci-Fi",
  "Slice of Life",
  "Sports",
  "Supernatural",
];

const years = Array.from({ length: 30 }, (_, i) => 2025 - i);

const sampleAnimes = [
  {
    id: 1,
    malId: 52991,
    title: "Sousou no Frieren",
    score: 9.29,
    type: "TV",
    episodes: 28,
    genres: ["Adventure", "Drama", "Fantasy"],
  },
  {
    id: 2,
    malId: 1,
    title: "Cowboy Bebop",
    score: 8.75,
    type: "TV",
    episodes: 26,
    genres: ["Action", "Adventure", "Sci-Fi"],
  },
  {
    id: 3,
    malId: 5114,
    title: "Fullmetal Alchemist: Brotherhood",
    score: 9.1,
    type: "TV",
    episodes: 64,
    genres: ["Action", "Adventure", "Drama"],
  },
  {
    id: 4,
    malId: 1535,
    title: "Death Note",
    score: 8.62,
    type: "TV",
    episodes: 37,
    genres: ["Mystery", "Supernatural"],
  },
  {
    id: 5,
    malId: 21,
    title: "One Punch Man",
    score: 8.5,
    type: "TV",
    episodes: 12,
    genres: ["Action", "Comedy"],
  },
  {
    id: 6,
    malId: 16498,
    title: "Attack on Titan",
    score: 8.53,
    type: "TV",
    episodes: 25,
    genres: ["Action", "Drama"],
  },
  {
    id: 7,
    malId: 30276,
    title: "One Punch Man S2",
    score: 7.45,
    type: "TV",
    episodes: 12,
    genres: ["Action", "Comedy"],
  },
  {
    id: 8,
    malId: 20,
    title: "Naruto",
    score: 8.0,
    type: "TV",
    episodes: 220,
    genres: ["Action", "Adventure"],
  },
];

export default function DiscoveryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [scoreRange, setScoreRange] = useState<number[]>([0, 10]);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const filteredAnimes = sampleAnimes.filter((anime) => {
    const matchesSearch = anime.title
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesGenre =
      selectedGenres.length === 0 ||
      selectedGenres.some((g) => anime.genres.includes(g));
    const matchesScore =
      anime.score >= scoreRange[0] && anime.score <= scoreRange[1];
    return matchesSearch && matchesGenre && matchesScore;
  });

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Discover <span className="gradient-text">Anime</span>
          </h1>
          <p className="text-foreground/60">
            Explore thousands of anime titles and find your next favorite
          </p>
        </motion.div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Filters Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:w-72 flex-shrink-0"
          >
            <Card className="bg-surface border border-white/5 sticky top-24">
              <CardBody className="p-6 space-y-6">
                {/* Search */}
                <div>
                  <label className="text-sm font-medium text-foreground/70 mb-2 block">
                    Search
                  </label>
                  <Input
                    placeholder="Search anime..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    variant="bordered"
                    classNames={{
                      inputWrapper: "bg-background/50 border-white/10",
                    }}
                    startContent={
                      <svg
                        className="w-4 h-4 text-foreground/40"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                      </svg>
                    }
                  />
                </div>

                {/* Genres */}
                <div>
                  <label className="text-sm font-medium text-foreground/70 mb-2 block">
                    Genres
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {genres.slice(0, 8).map((genre) => (
                      <Chip
                        key={genre}
                        size="sm"
                        variant={
                          selectedGenres.includes(genre) ? "solid" : "bordered"
                        }
                        color={
                          selectedGenres.includes(genre) ? "primary" : "default"
                        }
                        className="cursor-pointer"
                        onClick={() => {
                          setSelectedGenres((prev) =>
                            prev.includes(genre)
                              ? prev.filter((g) => g !== genre)
                              : [...prev, genre],
                          );
                        }}
                      >
                        {genre}
                      </Chip>
                    ))}
                  </div>
                </div>

                {/* Year */}
                <div>
                  <label className="text-sm font-medium text-foreground/70 mb-2 block">
                    Year
                  </label>
                  <Select
                    placeholder="Any year"
                    selectedKeys={selectedYear ? [selectedYear] : []}
                    onSelectionChange={(keys) =>
                      setSelectedYear(Array.from(keys)[0] as string)
                    }
                    variant="bordered"
                    classNames={{
                      trigger: "bg-background/50 border-white/10",
                    }}
                  >
                    {years.map((year) => (
                      <SelectItem key={year.toString()}>
                        {year.toString()}
                      </SelectItem>
                    ))}
                  </Select>
                </div>

                {/* Score Range */}
                <div>
                  <label className="text-sm font-medium text-foreground/70 mb-2 block">
                    Score: {scoreRange[0]} - {scoreRange[1]}
                  </label>
                  <Slider
                    step={0.5}
                    minValue={0}
                    maxValue={10}
                    value={scoreRange}
                    onChange={(value) => setScoreRange(value as number[])}
                    className="max-w-full"
                    color="primary"
                  />
                </div>

                {/* Clear Filters */}
                <Button
                  variant="light"
                  color="danger"
                  className="w-full"
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedGenres([]);
                    setSelectedYear("");
                    setScoreRange([0, 10]);
                  }}
                >
                  Clear Filters
                </Button>
              </CardBody>
            </Card>
          </motion.div>

          {/* Results */}
          <div className="flex-1">
            {/* Results Header */}
            <div className="flex items-center justify-between mb-6">
              <p className="text-foreground/60">
                Found{" "}
                <span className="text-primary font-semibold">
                  {filteredAnimes.length}
                </span>{" "}
                anime
              </p>
              <div className="flex gap-2">
                <Button
                  isIconOnly
                  variant={viewMode === "grid" ? "solid" : "light"}
                  color={viewMode === "grid" ? "primary" : "default"}
                  size="sm"
                  onClick={() => setViewMode("grid")}
                  aria-label="Grid view"
                >
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </Button>
                <Button
                  isIconOnly
                  variant={viewMode === "list" ? "solid" : "light"}
                  color={viewMode === "list" ? "primary" : "default"}
                  size="sm"
                  onClick={() => setViewMode("list")}
                  aria-label="List view"
                >
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </Button>
              </div>
            </div>

            {/* Anime Grid */}
            <div
              className={
                viewMode === "grid"
                  ? "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4"
                  : "space-y-3"
              }
            >
              {filteredAnimes.map((anime, index) => (
                <motion.div
                  key={anime.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link href={`/anime/${anime.malId}`}>
                    {viewMode === "grid" ? (
                      <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group">
                        <CardBody className="p-0">
                          <div className="aspect-[2/3] bg-surface-light relative overflow-hidden">
                            <div className="absolute inset-0 flex items-center justify-center text-4xl font-bold text-primary/30">
                              {anime.title.charAt(0)}
                            </div>
                            {/* Overlay on hover */}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                              <Button
                                size="sm"
                                color="primary"
                                className="w-full"
                              >
                                View Details
                              </Button>
                            </div>
                            {/* Score badge */}
                            <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-0.5 rounded text-xs font-semibold text-yellow-400 flex items-center gap-1">
                              <svg
                                className="w-3 h-3"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                              </svg>
                              {anime.score}
                            </div>
                          </div>
                          <div className="p-3">
                            <h3 className="font-semibold text-sm text-foreground line-clamp-2 group-hover:text-primary transition-colors">
                              {anime.title}
                            </h3>
                            <p className="text-xs text-foreground/50 mt-1">
                              {anime.type} • {anime.episodes} ep
                            </p>
                          </div>
                        </CardBody>
                      </Card>
                    ) : (
                      <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group">
                        <CardBody className="p-4">
                          <div className="flex gap-4">
                            <div className="w-20 aspect-[2/3] bg-surface-light rounded-lg flex-shrink-0 flex items-center justify-center text-2xl font-bold text-primary/30">
                              {anime.title.charAt(0)}
                            </div>
                            <div className="flex-1">
                              <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                                {anime.title}
                              </h3>
                              <p className="text-sm text-foreground/50 mt-1">
                                {anime.type} • {anime.episodes} episodes
                              </p>
                              <div className="flex items-center gap-2 mt-2">
                                <span className="text-yellow-400 text-sm font-semibold flex items-center gap-1">
                                  <svg
                                    className="w-3 h-3"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                  </svg>
                                  {anime.score}
                                </span>
                                {anime.genres.slice(0, 3).map((genre) => (
                                  <Chip
                                    key={genre}
                                    size="sm"
                                    variant="flat"
                                    className="text-xs"
                                  >
                                    {genre}
                                  </Chip>
                                ))}
                              </div>
                            </div>
                          </div>
                        </CardBody>
                      </Card>
                    )}
                  </Link>
                </motion.div>
              ))}
            </div>

            {/* Empty State */}
            {filteredAnimes.length === 0 && (
              <Card className="bg-surface border border-white/5">
                <CardBody className="p-12 text-center">
                  <svg
                    className="w-16 h-16 mx-auto text-foreground/20 mb-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <h3 className="text-xl font-semibold text-foreground/70 mb-2">
                    No anime found
                  </h3>
                  <p className="text-foreground/50">
                    Try adjusting your filters
                  </p>
                </CardBody>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
