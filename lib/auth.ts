import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
} from "amazon-cognito-identity-js";

const userPoolId = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID;
const clientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID;

if (!userPoolId || !clientId) {
  throw new Error(
    "COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID must be defined in environment variables"
  );
}

const poolData = {
  UserPoolId: userPoolId,
  ClientId: clientId,
};

export const userPool = new CognitoUserPool(poolData);

export const signUp = async (
  email: string,
  password: string,
  firstName: string,
  lastName: string
): Promise<string> => {
  const attributeList = [
    new CognitoUserAttribute({ Name: "email", Value: email }),
    new CognitoUserAttribute({ Name: "given_name", Value: firstName }),
    new CognitoUserAttribute({ Name: "family_name", Value: lastName }),
  ];

  return new Promise((resolve, reject) => {
    userPool.signUp(email, password, attributeList, [], (err) => {
      if (err) return reject(err.message || JSON.stringify(err));
      resolve(`Sign-up success. Confirmation email sent to ${email}`);
    });
  });
};

export const signIn = async (
  email: string,
  password: string
): Promise<{ accessToken: string; idToken: string }> => {
  const authDetails = new AuthenticationDetails({
    Username: email,
    Password: password,
  });

  const user = new CognitoUser({
    Username: email,
    Pool: userPool,
  });

  return new Promise((resolve, reject) => {
    user.authenticateUser(authDetails, {
      onSuccess: (session) => {
        const accessToken = session.getAccessToken().getJwtToken();
        const idToken = session.getIdToken().getJwtToken();
        resolve({ accessToken, idToken });
      },
      onFailure: (err) => {
        reject(err.message || JSON.stringify(err));
      },
    });
  });
};

export const signOut = () => {
  const user = userPool.getCurrentUser();
  if (user) user.signOut();
};
