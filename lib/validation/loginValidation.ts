export interface LoginForm {
  email: string;
  password: string;
}

export interface LoginFormErrors {
  email: string;
  password: string;
}

export function validateLoginForm(form: LoginForm): {
  isValid: boolean;
  errors: LoginFormErrors;
} {
  let isValid = true;
  const errors: LoginFormErrors = {
    email: "",
    password: "",
  };

  if (!form.email.trim()) {
    errors.email = "Email is required";
    isValid = false;
  }

  if (!form.password) {
    errors.password = "Password is required";
    isValid = false;
  }

  return { isValid, errors };
}