import { Suspense } from "react";
import VerifyEmailForm from "./verifyEmailForm";

export default function Verify() {
  return (
    <Suspense
      fallback={
        <div>
          <h1 className="text-center text-2xl font-bold mt-20">
            Loading...
          </h1>
        </div>
      }
    >
      <VerifyEmailForm />
    </Suspense>
  );
}
