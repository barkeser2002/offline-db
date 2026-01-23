"use client";

import { motion } from "framer-motion";
import { Button } from "@nextui-org/react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        {/* Animated 404 */}
        <motion.div
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", bounce: 0.5 }}
          className="mb-8"
        >
          <span className="text-9xl font-bold gradient-text">404</span>
        </motion.div>

        {/* Anime Character Emoji */}
        <motion.div
          animate={{
            y: [0, -10, 0],
          }}
          transition={{
            repeat: Infinity,
            duration: 2,
            ease: "easeInOut",
          }}
          className="text-6xl mb-6"
        >
          😵
        </motion.div>

        <h1 className="text-2xl font-bold text-foreground mb-2">
          Page Not Found
        </h1>
        <p className="text-foreground/60 mb-8 max-w-md mx-auto">
          Looks like this page got isekai'd to another dimension. Let's get you
          back to familiar territory.
        </p>

        <div className="flex justify-center gap-4">
          <Button as={Link} href="/" color="primary" size="lg">
            Go Home
          </Button>
          <Button as={Link} href="/discovery" variant="bordered" size="lg">
            Browse Anime
          </Button>
        </div>

        {/* Decorative Elements */}
        <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/10 rounded-full blur-[100px]" />
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-accent/10 rounded-full blur-[100px]" />
        </div>
      </motion.div>
    </div>
  );
}
