"use client";

import { motion } from "framer-motion";
import { Card, CardBody, Chip, Button } from "@nextui-org/react";
import Link from "next/link";

const blogPosts = [
  {
    id: 1,
    title: "Top 10 Anime of Winter 2026",
    excerpt:
      "Our picks for the best anime this season, from action-packed adventures to heartwarming slice of life...",
    date: "Jan 20, 2026",
    category: "Seasonal",
    readTime: "5 min",
    image: "",
  },
  {
    id: 2,
    title: "A Complete Guide to the Frieren Universe",
    excerpt:
      "Everything you need to know about the world, characters, and lore of Sousou no Frieren...",
    date: "Jan 18, 2026",
    category: "Guide",
    readTime: "12 min",
    image: "",
  },
  {
    id: 3,
    title: "Hidden Gems: Underrated Anime You Should Watch",
    excerpt:
      "These overlooked masterpieces deserve more attention. Here's our curated list...",
    date: "Jan 15, 2026",
    category: "Recommendations",
    readTime: "8 min",
    image: "",
  },
  {
    id: 4,
    title: "The Evolution of Isekai: From Origins to Now",
    excerpt:
      "Tracing the history of the isekai genre and how it became one of the most popular categories...",
    date: "Jan 12, 2026",
    category: "Analysis",
    readTime: "10 min",
    image: "",
  },
  {
    id: 5,
    title: "New Features: Episode Notifications & More",
    excerpt:
      "We've added new features to make your anime watching experience even better...",
    date: "Jan 10, 2026",
    category: "Updates",
    readTime: "3 min",
    image: "",
  },
];

const categories = [
  "All",
  "Seasonal",
  "Guide",
  "Recommendations",
  "Analysis",
  "Updates",
];

export default function BlogPage() {
  return (
    <div className="min-h-screen py-12">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-foreground mb-4">
            AniScrap <span className="gradient-text">Blog</span>
          </h1>
          <p className="text-foreground/60">
            News, guides, and insights from the anime world
          </p>
        </motion.div>

        {/* Categories */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-wrap justify-center gap-2 mb-8"
        >
          {categories.map((cat) => (
            <Chip
              key={cat}
              size="lg"
              variant={cat === "All" ? "solid" : "bordered"}
              color={cat === "All" ? "primary" : "default"}
              className="cursor-pointer"
            >
              {cat}
            </Chip>
          ))}
        </motion.div>

        {/* Featured Post */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <Link href={`/blog/${blogPosts[0].id}`}>
            <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group overflow-hidden">
              <CardBody className="p-0">
                <div className="grid md:grid-cols-2">
                  <div className="aspect-video md:aspect-auto bg-gradient-to-br from-primary/30 to-accent/30 flex items-center justify-center text-6xl font-bold text-white/20">
                    📝
                  </div>
                  <div className="p-6 md:p-8">
                    <Chip size="sm" color="warning" className="mb-3">
                      Featured
                    </Chip>
                    <h2 className="text-2xl font-bold text-foreground group-hover:text-primary transition-colors mb-3">
                      {blogPosts[0].title}
                    </h2>
                    <p className="text-foreground/60 mb-4">
                      {blogPosts[0].excerpt}
                    </p>
                    <div className="flex items-center gap-4 text-sm text-foreground/50">
                      <span>{blogPosts[0].date}</span>
                      <span>•</span>
                      <span>{blogPosts[0].readTime} read</span>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          </Link>
        </motion.div>

        {/* Posts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {blogPosts.slice(1).map((post, index) => (
            <motion.div
              key={post.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
            >
              <Link href={`/blog/${post.id}`}>
                <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group h-full">
                  <CardBody className="p-0">
                    <div className="aspect-video bg-surface-light flex items-center justify-center text-3xl text-foreground/20 group-hover:text-primary/30 transition-colors">
                      📄
                    </div>
                    <div className="p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Chip size="sm" variant="flat" color="primary">
                          {post.category}
                        </Chip>
                        <span className="text-xs text-foreground/40">
                          {post.readTime}
                        </span>
                      </div>
                      <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors mb-2 line-clamp-2">
                        {post.title}
                      </h3>
                      <p className="text-sm text-foreground/60 line-clamp-2 mb-3">
                        {post.excerpt}
                      </p>
                      <span className="text-xs text-foreground/40">
                        {post.date}
                      </span>
                    </div>
                  </CardBody>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Load More */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center mt-8"
        >
          <Button color="primary" variant="bordered" size="lg">
            Load More Posts
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
