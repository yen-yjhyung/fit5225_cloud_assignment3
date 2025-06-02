"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signIn } from "@/lib/auth";
import { validateLoginForm } from "@/lib/validation/loginValidation";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [formErrors, setFormErrors] = useState({
    email: "",
    password: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: any) => {
    e.preventDefault();

    setFormErrors({
      email: "",
      password: "",
    });

    setMessage("");

    const { isValid, errors } = validateLoginForm(form);
    if (!isValid) {
      setFormErrors(errors);
      setLoading(false);
      return;
    } else {
      setLoading(true);

      try {
        const { idToken } = await signIn(form.email, form.password);
        localStorage.setItem("token", idToken);
        router.push("/dashboard");
      } catch (err: any) {
        setMessage(`Login failed: ${err}`);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div
      className="flex items-center justify-center min-h-screen bg-gray-100 px-4 bg-no-repeat bg-cover bg-center"
      style={{ backgroundImage: "url('/bird_picture.jpg')" }}
    >
      <form
        onSubmit={handleSubmit}
        className="relative z-10 w-full max-w-sm rounded-lg bg-white/90 p-8 shadow-xl backdrop-blur"
      >
        <div className="flex flex-row items-center justify-center mb-6 gap-2">
          <div className="text-center">
            <img
              src="/bird.png"
              alt="BirdTag Logo"
              className="mx-auto mb-4 w-16 h-16"
            />
          </div>

          <h1 className="text-2xl font-bold text-center mb-6">BirdTag</h1>
        </div>

        <div className="space-y-4">
          <input
            placeholder="Email"
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.email && (
            <p className="text-red-500 text-sm">{formErrors.email}</p>
          )}
          <input
            type="password"
            placeholder="Password"
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.password && (
            <p className="text-red-500 text-sm">{formErrors.password}</p>
          )}
          <button
            type="submit"
            className={`cursor-pointer w-full ${
              loading ? "bg-red-400" : "bg-red-800"
            } text-white font-semibold py-3 px-4 rounded-lg`}
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </div>

        {message && (
          <p className="text-red-500 text-sm text-center mt-7">{message}</p>
        )}

        <p className="text-center text-sm mt-16">
          Don't have an account?{" "}
          <Link href="/auth/signup" className="text-red-800 underline">
            Sign up here
          </Link>
        </p>
      </form>
    </div>
  );
}
