// hooks/useRequireAuth.ts
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { userPool } from "@/lib/auth";
import { CognitoUserSession } from "amazon-cognito-identity-js";
import Error from "next/error";

export const useCurrentUser = () => {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const user = userPool.getCurrentUser();
    if (!user) {
      router.push("/auth/signup");
      return;
    }

    user.getSession((err: Error | null, session: CognitoUserSession) => {
      if (err || !session.isValid()) {
        router.push("/auth/signup");
      } else {
        setChecking(false);
      }
    });
  }, []);

  return { checking };
};
