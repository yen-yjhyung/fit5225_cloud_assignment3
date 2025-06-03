"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CognitoUser } from "amazon-cognito-identity-js";
import { userPool } from "@/lib/auth";
import {
  validateVerifyForm,
  VerifyForm,
  VerifyFormErrors,
} from "@/lib/validation/verifyValidation";

export default function VerifyEmail() {
  const [form, setForm] = useState<VerifyForm>({code: "" });
  const [formErrors, setFormErrors] = useState<VerifyFormErrors>({
    code: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const searchParams = useSearchParams();
  const emailFromQuery = searchParams.get("email") ?? "";

  const handleVerify = () => {
    const { isValid, errors } = validateVerifyForm(form);
    if (!isValid) {
      setFormErrors(errors);
      return;
    }

    setLoading(true);
    setMessage("");

    const user = new CognitoUser({
      Username: emailFromQuery,
      Pool: userPool,
    });

    user.confirmRegistration(form.code, true, (err, result) => {
      setLoading(false);
      if (err) {
        setMessage(`Error: ${err.message}`);
      } else {
        setMessage(`Success: ${result}`);
        router.push("/auth/login");
      }
    });
  };

  return (
    <div
      className="flex items-center justify-center min-h-screen bg-cover bg-center bg-no-repeat px-4"
      style={{ backgroundImage: "url('/bird_picture.jpg')" }}
    >
      <div className="relative z-10 w-full max-w-sm rounded-lg bg-white/90 p-8 shadow-xl backdrop-blur">
        <div className="text-center mb-6">
          <img
            src="/bird.png"
            alt="BirdTag Logo"
            className="mx-auto w-12 h-12 mb-2"
          />
          <h1 className="text-xl font-bold">Verify Your Email</h1>
        </div>

        <div className="space-y-4">
          <input
            readOnly
            disabled
            value={emailFromQuery}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          <input
            type="text"
            placeholder="Verification Code"
            onChange={(e) => setForm({ ...form, code: e.target.value })}
            className="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none"
          />
          {formErrors.code && (
            <p className="text-red-500 text-sm">{formErrors.code}</p>
          )}
          <button
            onClick={handleVerify}
            disabled={loading}
            className={`cursor-pointer w-full text-white font-semibold py-3 px-4 rounded-lg transition ${
              loading ? "bg-red-400" : "bg-red-800"
            }`}
          >
            {loading ? "Verifying..." : "Confirm Email"}
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
      </div>
    </div>
  );
}
