"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardBody, Input, Button } from "@nextui-org/react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);
    setIsSubmitted(true);
  };

  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4 py-12">
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-secondary/20 rounded-full blur-[100px] animate-pulse" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Card className="bg-surface/80 backdrop-blur-xl border border-white/10">
          <CardBody className="p-8">
            <div className="text-center mb-8">
              <Link href="/" className="inline-flex items-center gap-2 mb-6">
                <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
                  <span className="text-white font-bold text-xl">A</span>
                </div>
              </Link>

              {!isSubmitted ? (
                <>
                  <h1 className="text-2xl font-bold text-foreground mb-2">
                    Forgot Password?
                  </h1>
                  <p className="text-foreground/60">
                    Enter your email to reset your password
                  </p>
                </>
              ) : (
                <>
                  <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mx-auto mb-4">
                    <svg
                      className="w-8 h-8 text-success"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                  <h1 className="text-2xl font-bold text-foreground mb-2">
                    Check Your Email
                  </h1>
                  <p className="text-foreground/60">
                    We've sent password reset instructions to {email}
                  </p>
                </>
              )}
            </div>

            {!isSubmitted ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  type="email"
                  label="Email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  variant="bordered"
                  classNames={{
                    inputWrapper:
                      "bg-background/50 border-white/10 hover:border-primary/50",
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
                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                  }
                />

                <Button
                  type="submit"
                  color="primary"
                  size="lg"
                  className="w-full font-semibold"
                  isLoading={isLoading}
                >
                  Send Reset Link
                </Button>
              </form>
            ) : (
              <Button
                as={Link}
                href="/login"
                color="primary"
                variant="bordered"
                size="lg"
                className="w-full font-semibold"
              >
                Back to Login
              </Button>
            )}

            <p className="text-center mt-6 text-foreground/60">
              Remember your password?{" "}
              <Link
                href="/login"
                className="text-primary hover:text-primary-light font-semibold"
              >
                Sign In
              </Link>
            </p>
          </CardBody>
        </Card>
      </motion.div>
    </div>
  );
}
