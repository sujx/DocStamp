/** Vuelidate wrapper composable for form validation.

Provides a consistent validation interface across all form components:
- v$: Vuelidate validation state
- errors: reactive map of field → first error message
- validate(): trigger full validation pass
- reset(): clear validation state

Usage in a component:
    const rules = { text: { required } };
    const formData = reactive({ text: "" });
    const { v$, errors, validate } = useFormValidation(rules, formData);
*/

import { computed, reactive } from "vue";
import useVuelidate from "@vuelidate/core";

export interface ValidationRules {
  [field: string]: Record<string, unknown> | { [validator: string]: unknown };
}

export function useFormValidation(rules: ValidationRules, formData: Record<string, unknown>) {
  const v$ = useVuelidate(rules, formData, { $lazy: true });

  const errors = computed(() => {
    const errorMap: Record<string, string> = {};
    for (const key of Object.keys(v$.value)) {
      if (key.startsWith("$")) continue;
      const field = v$.value[key] as Record<string, unknown>;
      if (field.$error && Array.isArray(field.$errors) && field.$errors.length > 0) {
        const first = field.$errors[0] as { $message?: string };
        errorMap[key] = first.$message || "Invalid value";
      }
    }
    return errorMap;
  });

  async function validate(): Promise<boolean> {
    v$.value.$touch();
    await v$.value.$validate();
    return !v$.value.$error;
  }

  function reset() {
    v$.value.$reset();
  }

  return { v$, errors, validate, reset };
}
