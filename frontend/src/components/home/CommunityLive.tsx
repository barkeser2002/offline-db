"use client";

import { motion } from "framer-motion";
import { Card, CardBody, Avatar, Button } from "@nextui-org/react";
import Link from "next/link";

interface Activity {
  id: number;
  username: string;
  avatar?: string;
  action: string;
  anime: string;
  episode?: number;
  timestamp: string;
}

const sampleActivities: Activity[] = [
  {
    id: 1,
    username: "testuser",
    action: "Watched Episode 1 of",
    anime: "Cowboy Bebop",
    episode: 1,
    timestamp: "2m ago",
  },
  {
    id: 2,
    username: "anime_fan",
    action: "Added to watchlist",
    anime: "Sousou no Frieren",
    timestamp: "5m ago",
  },
  {
    id: 3,
    username: "otaku_master",
    action: "Rated 9/10",
    anime: "Attack on Titan",
    timestamp: "12m ago",
  },
];

export default function CommunityLive() {
  return (
    <section className="py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-1 h-6 bg-accent rounded-full" />
            <h2 className="text-2xl font-bold text-foreground">
              Community Live
            </h2>
            <div className="flex items-center gap-1 ml-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
              </span>
              <span className="text-xs text-foreground/50">LIVE</span>
            </div>
          </div>
          <Button
            as={Link}
            href="/community"
            variant="light"
            size="sm"
            className="text-primary"
            endContent={
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            }
          >
            VIEW ALL ACTIVITY
          </Button>
        </div>

        {/* Activity Feed */}
        <div className="space-y-3">
          {sampleActivities.map((activity, index) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="bg-surface/30 border border-white/5 hover:border-white/10 transition-colors">
                <CardBody className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <Avatar
                      name={activity.username}
                      size="sm"
                      className="bg-primary"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">
                        <span className="font-semibold text-primary">
                          {activity.username}
                        </span>{" "}
                        <span className="text-foreground/70">
                          {activity.action}
                        </span>{" "}
                        <span className="font-medium">{activity.anime}</span>
                      </p>
                    </div>
                    <span className="text-xs text-foreground/40 whitespace-nowrap">
                      {activity.timestamp}
                    </span>
                  </div>
                </CardBody>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
