export interface LoginForm {
  email: string;
  password: string;
}

export interface FormErrors {
  email: string;
  password: string;
}

export function validateLoginForm(form: LoginForm): {
  isValid: boolean;
  errors: FormErrors;
} {
  let isValid = true;
  const errors: FormErrors = {
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