import { cookies } from "next/headers";

export interface User {
  id: number;
  username: string;
  email: string;
  is_premium: boolean;
  date_joined: string;
  badges: any[]; // Define proper type if needed
  recent_history: any[]; // Define proper type if needed
}

export async function getCurrentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get("accessToken")?.value;

  if (!token) {
    return null;
  }

  try {
    const res = await fetch("http://localhost:8000/api/v1/profile/", {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!res.ok) {
      // Token might be expired or invalid
      return null;
    }

    const user = await res.json();
    return user;
  } catch (error) {
    console.error("Error fetching current user:", error);
    return null;
  }
}
