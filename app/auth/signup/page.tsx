"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { signUp } from "@/lib/auth";
import Link from "next/link";

import { validateSignupForm } from "@/lib/validation/signUpValidation";

export default function SignUp() {
  const [form, setForm] = useState({
    email: "",
    password: "",
    name: "",
    confirmPassword: "",
  });
  const [formErrors, setFormErrors] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: any) => {
    e.preventDefault();

    setFormErrors({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    });

    setMessage("");

    const { isValid, errors } = validateSignupForm(form);
    if (!isValid) {
      setFormErrors(errors);
      setLoading(false);
      return;
    } else {
      setLoading(true);

      try {
        const msg = await signUp(form.email, form.password, form.name);
        setMessage(msg);
        router.push("/auth/verify"); // Redirect to verification page
      } catch (err: any) {
        setMessage(`Error: ${err}`);
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
            type="text"
            placeholder="Name"
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.name && (
            <p className="text-red-500 text-sm">{formErrors.name}</p>
          )}
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
          <input
            type="password"
            placeholder="Confirm Password"
            onChange={(e) =>
              setForm({ ...form, confirmPassword: e.target.value })
            }
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.confirmPassword && (
            <p className="text-red-500 text-sm">{formErrors.confirmPassword}</p>
          )}
          <button
            type="submit"
            className={`cursor-pointer w-full ${
              loading ? "bg-red-400" : "bg-red-800"
            } text-white font-semibold py-3 px-4 rounded-lg`}
            disabled={loading}
          >
            {loading ? "Signing up..." : "Sign Up"}
          </button>
        </div>

        {message && (
          <p className="text-red-500 text-sm text-center">{message}</p>
        )}

        <p className="text-center text-sm mt-16">
          Already have an account?{" "}
          <Link href="/auth/login">
            <span className="text-red-800 underline">Sign in here</span>
          </Link>
        </p>
      </form>
    </div>
  );
}
