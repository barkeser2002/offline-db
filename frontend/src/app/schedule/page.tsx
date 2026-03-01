"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardBody, Chip, Tabs, Tab, Button } from "@nextui-org/react";
import Link from "next/link";

// Days of the week
const days = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

// Sample schedule data
const scheduleData: Record<
  string,
  Array<{
    id: number;
    malId: number;
    title: string;
    episode: number;
    time: string;
    coverImage?: string;
  }>
> = {
  Monday: [
    {
      id: 1,
      malId: 52991,
      title: "Sousou no Frieren",
      episode: 15,
      time: "23:00",
    },
  ],
  Tuesday: [
    { id: 2, malId: 21, title: "One Punch Man S3", episode: 8, time: "01:30" },
  ],
  Wednesday: [],
  Thursday: [
    {
      id: 3,
      malId: 5114,
      title: "My Hero Academia S7",
      episode: 12,
      time: "22:00",
    },
  ],
  Friday: [
    { id: 4, malId: 1535, title: "Demon Slayer S4", episode: 6, time: "23:45" },
    {
      id: 5,
      malId: 16498,
      title: "Jujutsu Kaisen S3",
      episode: 10,
      time: "00:30",
    },
  ],
  Saturday: [
    { id: 6, malId: 30276, title: "Blue Lock S2", episode: 14, time: "18:00" },
    { id: 7, malId: 20, title: "Solo Leveling S2", episode: 4, time: "23:00" },
  ],
  Sunday: [
    { id: 8, malId: 1, title: "Oshi no Ko S2", episode: 9, time: "22:30" },
  ],
};

export default function SchedulePage() {
  const today = new Date().toLocaleDateString("en-US", { weekday: "long" });
  const [selectedDay, setSelectedDay] = useState(today);

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
            Anime <span className="gradient-text">Schedule</span>
          </h1>
          <p className="text-foreground/60">
            Track upcoming anime episodes and never miss a release
          </p>
        </motion.div>

        {/* Day Tabs */}
        <Tabs
          selectedKey={selectedDay}
          onSelectionChange={(key) => setSelectedDay(key as string)}
          variant="underlined"
          classNames={{
            tabList: "gap-4 flex-wrap border-b border-white/10 pb-0",
            tab: "text-foreground/60 data-[selected=true]:text-primary font-medium py-4 px-2",
            cursor: "bg-primary",
          }}
        >
          {days.map((day) => (
            <Tab
              key={day}
              title={
                <div className="flex items-center gap-2">
                  {day === today && (
                    <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                  )}
                  <span>{day}</span>
                  {scheduleData[day]?.length > 0 && (
                    <Chip
                      size="sm"
                      variant="flat"
                      color="primary"
                      className="text-xs"
                    >
                      {scheduleData[day].length}
                    </Chip>
                  )}
                </div>
              }
            />
          ))}
        </Tabs>

        {/* Schedule Content */}
        <motion.div
          key={selectedDay}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mt-8"
        >
          {scheduleData[selectedDay]?.length > 0 ? (
            <div className="space-y-4">
              {scheduleData[selectedDay].map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link href={`/anime/${item.malId}`}>
                    <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all group">
                      <CardBody className="p-4">
                        <div className="flex items-center gap-4">
                          {/* Time */}
                          <div className="w-20 flex-shrink-0 text-center">
                            <span className="text-2xl font-bold text-primary">
                              {item.time}
                            </span>
                            <p className="text-xs text-foreground/50">JST</p>
                          </div>

                          {/* Divider */}
                          <div className="w-px h-16 bg-white/10" />

                          {/* Cover */}
                          <div className="w-24 aspect-[2/3] bg-surface-light rounded-lg flex-shrink-0 flex items-center justify-center text-2xl font-bold text-primary/30 group-hover:text-primary/50 transition-colors">
                            {item.title.charAt(0)}
                          </div>

                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-lg text-foreground group-hover:text-primary transition-colors truncate">
                              {item.title}
                            </h3>
                            <div className="flex items-center gap-3 mt-2">
                              <Chip size="sm" color="primary" variant="flat">
                                Episode {item.episode}
                              </Chip>
                              {selectedDay === today && (
                                <Chip size="sm" color="success" variant="dot">
                                  Airing Today
                                </Chip>
                              )}
                            </div>
                          </div>

                          {/* Bell Icon */}
                          <Button
                            isIconOnly
                            variant="bordered"
                            className="border-white/10 hover:border-primary/50 opacity-0 group-hover:opacity-100 transition-opacity"
                            aria-label={`Set reminder for ${item.title}`}
                          >
                            <svg
                              className="w-5 h-5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                              />
                            </svg>
                          </Button>
                        </div>
                      </CardBody>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          ) : (
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
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <h3 className="text-xl font-semibold text-foreground/70 mb-2">
                  No releases scheduled
                </h3>
                <p className="text-foreground/50">
                  Check back later for new episodes on {selectedDay}
                </p>
              </CardBody>
            </Card>
          )}
        </motion.div>

        {/* Legend */}
        <div className="mt-12 flex items-center justify-center gap-6 text-sm text-foreground/50">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            Today
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary" />
            Scheduled
          </div>
        </div>
      </div>
    </div>
  );
}
