"use client";

import { motion } from "framer-motion";
import { Card, CardBody } from "@nextui-org/react";

export default function TermsPage() {
  return (
    <div className="min-h-screen py-12">
      <div className="max-w-4xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Terms of Service
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
            <CardBody className="p-8 prose prose-invert max-w-none">
              <div className="space-y-6 text-foreground/80">
                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    1. Acceptance of Terms
                  </h2>
                  <p>
                    By accessing and using AniScrap, you accept and agree to be
                    bound by these Terms of Service. If you do not agree to
                    these terms, please do not use our service.
                  </p>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    2. Use of Service
                  </h2>
                  <p>
                    AniScrap provides an anime streaming and community platform.
                    You agree to use our service only for lawful purposes and in
                    accordance with these Terms.
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>
                      You must be at least 13 years old to use this service
                    </li>
                    <li>
                      You are responsible for maintaining the security of your
                      account
                    </li>
                    <li>You agree not to share your account credentials</li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    3. User Content
                  </h2>
                  <p>
                    Users may submit reviews, comments, and other content. You
                    retain ownership of your content but grant us a license to
                    use, display, and distribute it on our platform.
                  </p>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    4. Prohibited Activities
                  </h2>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Attempting to bypass security measures</li>
                    <li>Uploading malicious content</li>
                    <li>Harassing other users</li>
                    <li>
                      Distributing copyrighted material without permission
                    </li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    5. Intellectual Property
                  </h2>
                  <p>
                    All anime content is owned by their respective creators and
                    studios. AniScrap does not claim ownership of any anime
                    content displayed on the platform.
                  </p>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    6. Limitation of Liability
                  </h2>
                  <p>
                    AniScrap is provided "as is" without warranties. We are not
                    liable for any damages arising from your use of the service.
                  </p>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    7. Changes to Terms
                  </h2>
                  <p>
                    We reserve the right to modify these terms at any time.
                    Continued use of the service after changes constitutes
                    acceptance of the new terms.
                  </p>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    8. Contact
                  </h2>
                  <p>
                    For questions about these Terms, please contact us at
                    legal@aniscrap.com
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
