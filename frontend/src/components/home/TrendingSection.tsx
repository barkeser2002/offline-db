"use client";

import { motion } from "framer-motion";
import { Card, CardBody, Chip } from "@nextui-org/react";
import Link from "next/link";
import { Anime } from "@/services/api";

interface TrendingCardProps {
  anime: Anime;
  index: number;
}

export function TrendingCard({ anime, index }: TrendingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Link href={`/anime/${anime.mal_id}`}>
        <Card
          className="group relative bg-surface border border-white/5 hover:border-primary/50 transition-all duration-300 overflow-hidden"
          isPressable
        >
          <CardBody className="p-0">
            {/* Poster Container */}
            <div className="relative aspect-[2/3] overflow-hidden">
              {/* Image */}
              <div
                className="absolute inset-0 bg-surface-light transition-transform duration-500 group-hover:scale-110"
                style={{
                  backgroundImage: anime.cover_image
                    ? `url(${anime.cover_image})`
                    : undefined,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                }}
              />

              {/* Fallback skeleton if no image */}
              {!anime.cover_image && (
                <div className="absolute inset-0 skeleton" />
              )}

              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity" />

              {/* Glow Effect on Hover */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="absolute inset-0 bg-primary/10" />
                <div className="absolute -inset-1 bg-gradient-to-t from-primary/30 to-transparent blur-xl" />
              </div>

              {/* Type Badge */}
              <div className="absolute top-2 left-2 z-10">
                <Chip
                  size="sm"
                  color="primary"
                  variant="solid"
                  className="text-xs font-semibold"
                >
                  {anime.type}
                </Chip>
              </div>

              {/* Score Badge */}
              <div className="absolute top-2 right-2 z-10">
                <div className="flex items-center gap-1 bg-black/60 backdrop-blur-sm rounded-full px-2 py-1">
                  <svg
                    className="w-3 h-3 text-yellow-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  <span className="text-xs font-semibold text-white">
                    {anime.score}
                  </span>
                </div>
              </div>

              {/* Title Overlay */}
              <div className="absolute bottom-0 left-0 right-0 p-3 z-10">
                <h3 className="font-semibold text-white text-sm line-clamp-2 group-hover:text-primary-light transition-colors">
                  {anime.title}
                </h3>
              </div>
            </div>
          </CardBody>
        </Card>
      </Link>
    </motion.div>
  );
}

interface TrendingSectionProps {
  items?: Anime[];
}

export default function TrendingSection({ items = [] }: TrendingSectionProps) {
  if (!items || items.length === 0) return null;

  return (
    <section className="py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Section Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-1 h-6 bg-primary rounded-full" />
          <h2 className="text-2xl font-bold text-foreground">Trending Now</h2>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {items.map((anime, index) => (
            <TrendingCard key={anime.id} anime={anime} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}
