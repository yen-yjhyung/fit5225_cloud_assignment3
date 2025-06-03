"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { signUp } from "@/lib/auth";
import {
  SignupForm,
  SignUpFormErrors,
  validateSignupForm,
} from "@/lib/validation/signUpValidation";

import { FiEye, FiEyeOff } from "react-icons/fi";

export default function SignUp() {
  const [form, setForm] = useState<SignupForm>({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [formErrors, setFormErrors] = useState<SignUpFormErrors>({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (e: any) => {
    e.preventDefault();

    setFormErrors({
      firstName: "",
      lastName: "",
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
        const msg = await signUp(
          form.email,
          form.password,
          form.firstName,
          form.lastName
        );
        setMessage(msg);
        router.push(`/auth/verify?email=${encodeURIComponent(form.email)}`); // Redirect to verification page
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
            placeholder="First Name"
            onChange={(e) => setForm({ ...form, firstName: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.firstName && (
            <p className="text-red-500 text-sm">{formErrors.firstName}</p>
          )}
          <input
            type="text"
            placeholder="Last Name"
            onChange={(e) => setForm({ ...form, lastName: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.lastName && (
            <p className="text-red-500 text-sm">{formErrors.lastName}</p>
          )}
          <input
            placeholder="Email"
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.email && (
            <p className="text-red-500 text-sm">{formErrors.email}</p>
          )}
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="cursor-pointer absolute right-3 top-1/2 transform -translate-y-1/2"
              aria-label="Toggle password visibility"
            >
              {showPassword ? (
                <FiEyeOff className="text-red-800" size={20} />
              ) : (
                <FiEye className="text-red-800" size={20} />
              )}
            </button>
          </div>
          {formErrors.password && (
            <p className="text-red-500 text-sm">{formErrors.password}</p>
          )}
          <div className="relative">
            <input
              type={showConfirmPassword ? "text" : "password"}
              placeholder="Confirm Password"
              onChange={(e) =>
                setForm({ ...form, confirmPassword: e.target.value })
              }
              className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none pr-12"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className=" cursor-pointer absolute right-3 top-1/2 transform -translate-y-1/2"
              aria-label="Toggle confirm password visibility"
            >
              {showConfirmPassword ? (
                <FiEyeOff className="text-red-800" size={20} />
              ) : (
                <FiEye className="text-red-800" size={20} />
              )}
            </button>
          </div>
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
          <p
            className={`text-sm text-center mt-7 ${
              message.startsWith("Error") ? "text-red-500" : "text-green-600"
            }`}
          >
            {message}
          </p>
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
