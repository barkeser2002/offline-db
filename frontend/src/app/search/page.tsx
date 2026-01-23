"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Card, CardBody, Input, Chip, Tabs, Tab } from "@nextui-org/react";
import Link from "next/link";

// Sample search results
const sampleResults = {
  anime: [
    {
      id: 1,
      malId: 52991,
      title: "Sousou no Frieren",
      type: "TV",
      score: 9.29,
    },
    { id: 2, malId: 1, title: "Cowboy Bebop", type: "TV", score: 8.75 },
    {
      id: 3,
      malId: 5114,
      title: "Fullmetal Alchemist: Brotherhood",
      type: "TV",
      score: 9.1,
    },
  ],
  characters: [
    { id: 1, name: "Frieren", anime: "Sousou no Frieren" },
    { id: 2, name: "Spike Spiegel", anime: "Cowboy Bebop" },
    { id: 3, name: "Edward Elric", anime: "Fullmetal Alchemist" },
  ],
};

function SearchContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  const [query, setQuery] = useState(initialQuery);
  const [selectedTab, setSelectedTab] = useState("all");

  return (
    <>
      {/* Search Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-foreground mb-6">Search</h1>
        <Input
          type="search"
          placeholder="Search anime, characters..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          size="lg"
          variant="bordered"
          classNames={{
            inputWrapper: "bg-surface border-white/10 hover:border-primary/50",
          }}
          startContent={
            <svg
              className="w-5 h-5 text-foreground/40"
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
      </motion.div>

      {query && (
        <>
          {/* Results Tabs */}
          <Tabs
            selectedKey={selectedTab}
            onSelectionChange={(key) => setSelectedTab(key as string)}
            variant="underlined"
            classNames={{
              tabList: "border-b border-white/10 pb-0",
              tab: "text-foreground/60 data-[selected=true]:text-primary font-medium py-4",
              cursor: "bg-primary",
            }}
          >
            <Tab
              key="all"
              title={
                <div className="flex items-center gap-2">
                  All{" "}
                  <Chip size="sm" variant="flat">
                    {sampleResults.anime.length +
                      sampleResults.characters.length}
                  </Chip>
                </div>
              }
            />
            <Tab
              key="anime"
              title={
                <div className="flex items-center gap-2">
                  Anime{" "}
                  <Chip size="sm" variant="flat">
                    {sampleResults.anime.length}
                  </Chip>
                </div>
              }
            />
            <Tab
              key="characters"
              title={
                <div className="flex items-center gap-2">
                  Characters{" "}
                  <Chip size="sm" variant="flat">
                    {sampleResults.characters.length}
                  </Chip>
                </div>
              }
            />
          </Tabs>

          {/* Results */}
          <div className="mt-6 space-y-6">
            {/* Anime Results */}
            {(selectedTab === "all" || selectedTab === "anime") && (
              <div>
                <h2 className="text-lg font-semibold text-foreground mb-4">
                  Anime
                </h2>
                <div className="space-y-3">
                  {sampleResults.anime.map((anime, index) => (
                    <motion.div
                      key={anime.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Link href={`/anime/${anime.malId}`}>
                        <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group">
                          <CardBody className="p-4">
                            <div className="flex items-center gap-4">
                              <div className="w-16 aspect-[2/3] bg-surface-light rounded flex items-center justify-center text-xl font-bold text-primary/30 group-hover:text-primary/50 transition-colors">
                                {anime.title.charAt(0)}
                              </div>
                              <div className="flex-1">
                                <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                                  {anime.title}
                                </h3>
                                <div className="flex items-center gap-2 mt-1">
                                  <Chip size="sm" variant="flat">
                                    {anime.type}
                                  </Chip>
                                  <span className="text-yellow-400 text-sm">
                                    ★ {anime.score}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </CardBody>
                        </Card>
                      </Link>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Character Results */}
            {(selectedTab === "all" || selectedTab === "characters") && (
              <div>
                <h2 className="text-lg font-semibold text-foreground mb-4">
                  Characters
                </h2>
                <div className="space-y-3">
                  {sampleResults.characters.map((char, index) => (
                    <motion.div
                      key={char.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group">
                        <CardBody className="p-4">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-surface-light flex items-center justify-center text-lg font-bold text-primary/30 group-hover:text-primary/50 transition-colors">
                              {char.name.charAt(0)}
                            </div>
                            <div>
                              <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                                {char.name}
                              </h3>
                              <p className="text-sm text-foreground/60">
                                from {char.anime}
                              </p>
                            </div>
                          </div>
                        </CardBody>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Empty State */}
      {!query && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
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
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <h3 className="text-xl font-semibold text-foreground/70 mb-2">
            Start Searching
          </h3>
          <p className="text-foreground/50">
            Enter a query to search for anime or characters
          </p>
        </motion.div>
      )}
    </>
  );
}

export default function SearchPage() {
  return (
    <div className="min-h-screen py-8">
      <div className="max-w-5xl mx-auto px-4">
        <Suspense
          fallback={
            <div className="animate-pulse">
              <div className="h-12 bg-surface rounded-lg mb-8" />
              <div className="space-y-4">
                <div className="h-24 bg-surface rounded-lg" />
                <div className="h-24 bg-surface rounded-lg" />
              </div>
            </div>
          }
        >
          <SearchContent />
        </Suspense>
      </div>
    </div>
  );
}
