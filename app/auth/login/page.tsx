"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signIn } from "@/lib/auth";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: any) => {
    setLoading(true);
    e.preventDefault();
    try {
      const { idToken } = await signIn(form.email, form.password);
      localStorage.setItem("token", idToken);
      router.push("/dashboard");
    } catch (err: any) {
      setMessage(`Login failed: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-white rounded-lg shadow p-8 space-y-6"
      >
        <div className="text-center">
          <img
            src="/bird.png"
            alt="BirdTag Logo"
            className="mx-auto mb-4 w-16 h-16"
          />
        </div>

        <div className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            required
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          <input
            type="password"
            placeholder="Password"
            required
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          <button
            type="submit"
            className={`cursor-pointer w-full ${loading? 'bg-red-400' : 'bg-red-800'} hover:bg-red-700 text-white font-semibold py-3 px-4 rounded-lg`}
            disabled={loading}
          >
            {loading? 'Logging in...' : 'Login'}
          </button>
        </div>

        {message && <p className="text-red-500 text-sm text-center">{message}</p>}

        <p className="text-center text-sm">
          Don't have an account?{" "}
          <Link href="/auth/signup" className="text-blue-600 underline">
            Sign up here
          </Link>
        </p>
      </form>
    </div>
  );
}
