"use client";

import { motion } from "framer-motion";
import { Card, CardBody, Button } from "@nextui-org/react";

export default function DMCAPage() {
  return (
    <div className="min-h-screen py-12">
      <div className="max-w-4xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold text-foreground mb-2">
            DMCA Policy
          </h1>
          <p className="text-foreground/60 mb-8">
            Digital Millennium Copyright Act Notice
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
                    Copyright Infringement Notice
                  </h2>
                  <p>
                    AniScrap respects the intellectual property rights of
                    others. If you believe that any content on our platform
                    infringes your copyright, please notify us.
                  </p>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    How to File a DMCA Notice
                  </h2>
                  <p>To file a valid DMCA notice, please provide:</p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Your physical or electronic signature</li>
                    <li>
                      Identification of the copyrighted work claimed to be
                      infringed
                    </li>
                    <li>
                      Identification of the infringing material and its location
                    </li>
                    <li>Your contact information (address, phone, email)</li>
                    <li>A statement of good faith belief</li>
                    <li>A statement of accuracy under penalty of perjury</li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    Counter-Notification
                  </h2>
                  <p>
                    If you believe your content was wrongly removed, you may
                    submit a counter-notification including:
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Your physical or electronic signature</li>
                    <li>
                      Identification of the removed material and its former
                      location
                    </li>
                    <li>
                      A statement under penalty of perjury that removal was a
                      mistake
                    </li>
                    <li>Your name, address, and phone number</li>
                    <li>Consent to local federal court jurisdiction</li>
                  </ul>
                </section>

                <section>
                  <h2 className="text-xl font-semibold text-foreground mb-3">
                    Contact Information
                  </h2>
                  <p className="mb-4">Send DMCA notices to:</p>
                  <Card className="bg-background/50 border border-white/10">
                    <CardBody className="p-4">
                      <p className="font-medium text-foreground">
                        AniScrap DMCA Agent
                      </p>
                      <p>Email: dmca@aniscrap.com</p>
                      <p>Response time: 24-48 hours</p>
                    </CardBody>
                  </Card>
                </section>

                <div className="pt-4">
                  <Button color="primary" variant="bordered">
                    Submit DMCA Notice
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
