// hooks/useAuthTokens.ts
import { useEffect, useState } from 'react';
import { userPool } from '@/lib/auth';
import { CognitoUserSession } from 'amazon-cognito-identity-js';

export interface Tokens {
  idToken: string | null;
  accessToken: string | null;
  email?: string;
  name?: string;
  user_id?: string;
}

export const useAuthTokens = (): Tokens => {
  const [tokens, setTokens] = useState<Tokens>({
    idToken: null,
    accessToken: null,
  });

  useEffect(() => {
    const user = userPool.getCurrentUser();

    if (user) {
      user.getSession((err: Error | null, session: CognitoUserSession) => {
        if (err || !session.isValid()) return;

        const idTokenObj = session.getIdToken();
        const accessTokenObj = session.getAccessToken();

        const decodedIdToken = idTokenObj.decodePayload?.();
        setTokens({
          idToken: idTokenObj.getJwtToken(),
          accessToken: accessTokenObj.getJwtToken(),
          email: decodedIdToken?.email,
          name: decodedIdToken?.given_name,
          user_id: decodedIdToken?.sub,
        });
      });
    }
  }, []);

  return tokens;
};
