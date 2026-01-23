"use client";

import { motion } from "framer-motion";
import { Card, CardBody } from "@nextui-org/react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen py-12">
      <div className="max-w-4xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Privacy Policy
          </h1>
          <p className="text-foreground/60 mb-8">
            Last updated: January 23, 2026
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-surface border border-white/5">
            <CardBody className="p-8">
              <div className="space-y-6 text-foreground/80">
                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    Information We Collect
                  </h2>
                  <p>
                    We collect information you provide directly to us,
                    including:
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Account information (username, email, password)</li>
                    <li>Profile information (avatar, preferences)</li>
                    <li>Watch history and lists</li>
                    <li>Reviews and comments</li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    How We Use Your Information
                  </h2>
                  <ul className="list-disc list-inside space-y-1">
                    <li>To provide and improve our services</li>
                    <li>To personalize your experience</li>
                    <li>To send notifications about new episodes</li>
                    <li>To communicate with you about your account</li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    Cookies and Tracking
                  </h2>
                  <p>We use cookies and similar technologies to:</p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Keep you logged in</li>
                    <li>Remember your preferences</li>
                    <li>Track watch progress</li>
                    <li>Analyze site usage</li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    Data Security
                  </h2>
                  <p>
                    We implement appropriate security measures to protect your
                    personal information. However, no method of transmission
                    over the Internet is 100% secure.
                  </p>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    Your Rights
                  </h2>
                  <p>You have the right to:</p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Access your personal data</li>
                    <li>Correct inaccurate data</li>
                    <li>Request deletion of your data</li>
                    <li>Export your data</li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    Contact Us
                  </h2>
                  <p>
                    For privacy-related inquiries, contact us at
                    privacy@aniscrap.com
                  </p>
                </section>
              </div>
            </CardBody>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
