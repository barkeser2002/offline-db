"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button, Chip } from "@nextui-org/react";
import Link from "next/link";
import { Anime } from "@/services/api";

interface HeroSectionProps {
  slides?: Anime[]; // Make optional to prevent crash if undefined
}

export default function HeroSection({ slides = [] }: HeroSectionProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // If no slides, show nothing or skeleton. Ideally parent handles loading.
  if (!slides || slides.length === 0) {
    return (
      <section className="relative h-[70vh] min-h-[500px] overflow-hidden bg-surface flex items-center justify-center">
        <div className="text-foreground/50">Loading content...</div>
      </section>
    );
  }

  useEffect(() => {
    if (isPaused) return;

    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 8000);

    return () => clearInterval(timer);
  }, [slides.length, isPaused]);

  const slide = slides[currentSlide];

  return (
    <section
      className="relative h-[70vh] min-h-[500px] overflow-hidden"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onFocus={() => setIsPaused(true)}
      onBlur={(e) => {
        // Only resume if focus moves outside the section
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          setIsPaused(false);
        }
      }}
    >
      {/* Background Image with Overlay */}
      <AnimatePresence mode="wait">
        <motion.div
          key={slide.id}
          initial={{ opacity: 0, scale: 1.1 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8 }}
          className="absolute inset-0 z-0"
        >
          <div
            className="absolute inset-0 bg-cover bg-center"
            style={{
              backgroundImage: `url(${slide.cover_image || "/placeholder-banner.jpg"})`,
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-background via-background/60 to-transparent" />
        </motion.div>
      </AnimatePresence>

      {/* Content */}
      <div className="relative z-10 h-full max-w-7xl mx-auto px-4 flex items-end pb-24 md:pb-32">
        <div className="max-w-2xl">
          <motion.div
            key={`content-${slide.id}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {/* Tags */}
            <div className="flex flex-wrap gap-2 mb-4">
              <Chip
                color="primary"
                variant="solid"
                className="uppercase font-bold"
              >
                {slide.type}
              </Chip>
              <Chip
                variant="bordered"
                className="text-white border-white/30 backdrop-blur-md"
              >
                {slide.status}
              </Chip>
              <div className="flex items-center gap-1 bg-yellow-500/20 backdrop-blur-md px-3 py-1 rounded-full border border-yellow-500/30">
                <span className="text-yellow-400">★</span>
                <span className="font-bold text-yellow-400">{slide.score}</span>
              </div>
            </div>

            {/* Title */}
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-2 leading-tight">
              {slide.title}
            </h1>

            {/* Description (Not in AnimeListSerializer but we can mock or use mal_id to fetch detailed if needed, 
               but for now we likely don't have description in list view. We'll show genres.) */}
            <div className="flex flex-wrap gap-2 mb-6">
              {slide.genres?.map((g) => (
                <span key={g.id} className="text-white/80 text-sm">
                  {g.name} •
                </span>
              ))}
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-4">
              <Button
                as={Link}
                href={`/watch/${slide.mal_id}/1`}
                size="lg"
                color="primary"
                className="font-bold px-8"
                startContent={
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                    aria-hidden="true"
                  >
                    <path d="M4 4l12 6-12 6V4z" />
                  </svg>
                }
              >
                Watch Now
              </Button>
              <Button
                as={Link}
                href={`/anime/${slide.mal_id}`}
                size="lg"
                variant="bordered"
                className="font-semibold text-white border-white/30 hover:bg-white/10"
              >
                Details
              </Button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Slide Indicators */}
      <div className="absolute bottom-8 right-8 z-20 flex gap-2">
        {slides.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentSlide(idx)}
            aria-label={`Go to slide ${idx + 1}`}
            aria-current={idx === currentSlide ? "true" : undefined}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              idx === currentSlide
                ? "w-8 bg-primary"
                : "w-2 bg-white/30 hover:bg-white/50"
            }`}
          />
        ))}
      </div>
    </section>
  );
}
