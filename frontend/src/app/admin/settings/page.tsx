"use client";

import { Card, CardBody, Switch, Input, Button } from "@nextui-org/react";

export default function AdminSettingsPage() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-foreground mb-6">
        System Settings
      </h1>

      <div className="space-y-6">
        {/* General Settings */}
        <Card className="bg-surface border border-white/5">
          <CardBody className="p-6 space-y-4">
            <h3 className="text-lg font-semibold text-foreground mb-2">
              General Configuration
            </h3>
            <Input
              label="Site Name"
              defaultValue="AniScrap"
              variant="bordered"
            />
            <Input
              label="Support Email"
              defaultValue="support@aniscrap.com"
              variant="bordered"
            />
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-foreground">Maintenance Mode</p>
                <p className="text-sm text-foreground/50">
                  Disable site access for regular users
                </p>
              </div>
              <Switch />
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-foreground">User Registration</p>
                <p className="text-sm text-foreground/50">
                  Allow new users to sign up
                </p>
              </div>
              <Switch defaultSelected />
            </div>
          </CardBody>
        </Card>

        {/* API Settings */}
        <Card className="bg-surface border border-white/5">
          <CardBody className="p-6 space-y-4">
            <h3 className="text-lg font-semibold text-foreground mb-2">
              API Keys
            </h3>
            <Input
              label="DeepL API Key"
              type="password"
              defaultValue="************************"
              variant="bordered"
            />
            <Input
              label="Jikan API Limit (Rate)"
              defaultValue="3"
              type="number"
              variant="bordered"
            />
          </CardBody>
        </Card>

        <div className="flex justify-end gap-4">
          <Button variant="flat" color="danger">
            Reset Defaults
          </Button>
          <Button color="primary">Save Changes</Button>
        </div>
      </div>
    </div>
  );
}
