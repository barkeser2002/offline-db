"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardBody, Button, Chip, Tabs, Tab } from "@nextui-org/react";
import Link from "next/link";

const collections = [
  {
    id: 1,
    name: "Epic Adventures",
    description: "Action-packed journeys with unforgettable heroes",
    count: 15,
    coverImages: ["", "", "", ""],
    curator: "AniScrap",
  },
  {
    id: 2,
    name: "Mind-Bending Thrillers",
    description: "Psychological masterpieces that keep you guessing",
    count: 12,
    coverImages: ["", "", "", ""],
    curator: "AniScrap",
  },
  {
    id: 3,
    name: "Heartwarming Slice of Life",
    description: "Relaxing anime for the soul",
    count: 20,
    coverImages: ["", "", "", ""],
    curator: "AniScrap",
  },
  {
    id: 4,
    name: "Classic Must-Watch",
    description: "Timeless anime everyone should see",
    count: 25,
    coverImages: ["", "", "", ""],
    curator: "AniScrap",
  },
  {
    id: 5,
    name: "Hidden Gems",
    description: "Underrated anime that deserve more love",
    count: 18,
    coverImages: ["", "", "", ""],
    curator: "community",
  },
  {
    id: 6,
    name: "Isekai Adventures",
    description: "Best transported to another world stories",
    count: 22,
    coverImages: ["", "", "", ""],
    curator: "community",
  },
];

const myLists = [
  { id: 1, name: "Watching", count: 5, color: "primary" },
  { id: 2, name: "Completed", count: 42, color: "success" },
  { id: 3, name: "Plan to Watch", count: 128, color: "warning" },
  { id: 4, name: "On Hold", count: 8, color: "secondary" },
  { id: 5, name: "Dropped", count: 3, color: "danger" },
];

export default function CollectionsPage() {
  const [selectedTab, setSelectedTab] = useState("featured");

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
            Anime <span className="gradient-text">Collections</span>
          </h1>
          <p className="text-foreground/60">
            Curated lists and your personal anime library
          </p>
        </motion.div>

        {/* My Lists Quick Access */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="text-xl font-semibold text-foreground mb-4">
            My Lists
          </h2>
          <div className="flex flex-wrap gap-3">
            {myLists.map((list) => (
              <Link
                key={list.id}
                href={`/collections/my/${list.name.toLowerCase().replace(" ", "-")}`}
              >
                <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all cursor-pointer group">
                  <CardBody className="p-4 flex flex-row items-center gap-3">
                    <div className={`w-3 h-3 rounded-full bg-${list.color}`} />
                    <span className="font-medium text-foreground group-hover:text-primary transition-colors">
                      {list.name}
                    </span>
                    <Chip size="sm" variant="flat">
                      {list.count}
                    </Chip>
                  </CardBody>
                </Card>
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Tabs */}
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
          <Tab key="featured" title="Featured Collections">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
              {collections
                .filter((c) => c.curator === "AniScrap")
                .map((collection, index) => (
                  <motion.div
                    key={collection.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group overflow-hidden">
                      <CardBody className="p-0">
                        {/* Cover Grid */}
                        <div className="grid grid-cols-2 gap-1 h-32">
                          {collection.coverImages.map((_, i) => (
                            <div
                              key={i}
                              className="bg-surface-light flex items-center justify-center text-primary/30 font-bold text-lg group-hover:bg-primary/10 transition-colors"
                            >
                              {collection.name.charAt(i) || "?"}
                            </div>
                          ))}
                        </div>
                        <div className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                              {collection.name}
                            </h3>
                            <Chip size="sm" color="primary" variant="flat">
                              {collection.count} anime
                            </Chip>
                          </div>
                          <p className="text-sm text-foreground/60 line-clamp-2">
                            {collection.description}
                          </p>
                          <div className="flex items-center gap-2 mt-3">
                            <Chip size="sm" variant="dot" color="warning">
                              Staff Pick
                            </Chip>
                          </div>
                        </div>
                      </CardBody>
                    </Card>
                  </motion.div>
                ))}
            </div>
          </Tab>

          <Tab key="community" title="Community Collections">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
              {collections
                .filter((c) => c.curator === "community")
                .map((collection, index) => (
                  <motion.div
                    key={collection.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group overflow-hidden">
                      <CardBody className="p-0">
                        <div className="grid grid-cols-2 gap-1 h-32">
                          {collection.coverImages.map((_, i) => (
                            <div
                              key={i}
                              className="bg-surface-light flex items-center justify-center text-accent/30 font-bold text-lg group-hover:bg-accent/10 transition-colors"
                            >
                              {collection.name.charAt(i) || "?"}
                            </div>
                          ))}
                        </div>
                        <div className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                              {collection.name}
                            </h3>
                            <Chip size="sm" color="secondary" variant="flat">
                              {collection.count} anime
                            </Chip>
                          </div>
                          <p className="text-sm text-foreground/60 line-clamp-2">
                            {collection.description}
                          </p>
                        </div>
                      </CardBody>
                    </Card>
                  </motion.div>
                ))}
            </div>
          </Tab>

          <Tab key="create" title="+ Create Collection">
            <div className="mt-6">
              <Card className="bg-surface border border-white/5 max-w-xl">
                <CardBody className="p-8 text-center">
                  <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4">
                    <svg
                      className="w-8 h-8 text-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    Create Your Collection
                  </h3>
                  <p className="text-foreground/60 mb-6">
                    Curate your own anime list and share it with the community
                  </p>
                  <Button color="primary" size="lg">
                    Get Started
                  </Button>
                </CardBody>
              </Card>
            </div>
          </Tab>
        </Tabs>
      </div>
    </div>
  );
}
