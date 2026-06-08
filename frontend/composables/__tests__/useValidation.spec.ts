/**
 * Tests for useValidation composable (Vuelidate wrapper).
 *
 * Covers: required fields, minLength, custom validators,
 * validate(), reset(), and error mapping.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { useFormValidation } from "../useValidation";
import { required, minLength, email } from "@vuelidate/validators";
import { reactive } from "vue";

describe("useValidation", () => {
  let formData: Record<string, unknown>;

  beforeEach(() => {
    formData = reactive({
      name: "",
      email: "",
      age: 0,
    });
  });

  it("应该对空字段返回 required 错误", async () => {
    const rules = { name: { required } };
    const { errors, validate } = useFormValidation(rules, formData);

    const valid = await validate();

    expect(valid).toBe(false);
    expect(errors.value.name).toBeTruthy();
  });

  it("应该对有效输入返回成功", async () => {
    formData.name = "测试名称";
    const rules = { name: { required, minLength: minLength(2) } };
    const { errors, validate } = useFormValidation(rules, formData);

    const valid = await validate();

    expect(valid).toBe(true);
    expect(errors.value.name).toBeFalsy();
  });

  it("minLength 校验失败时应该返回错误", async () => {
    formData.name = "A"; // too short
    const rules = { name: { required, minLength: minLength(3) } };
    const { errors, validate } = useFormValidation(rules, formData);

    const valid = await validate();

    expect(valid).toBe(false);
    expect(errors.value.name).toBeTruthy();
  });

  it("reset() 应该清除所有校验状态", async () => {
    const rules = { name: { required } };
    const { errors, validate, reset } = useFormValidation(rules, formData);

    // First, trigger a validation failure
    await validate();
    expect(errors.value.name).toBeTruthy();

    // Reset and re-check
    reset();
    // After reset, the Vuelidate state should be clean
    expect(errors.value.name).toBeFalsy();
  });

  it("多个字段校验失败时 errors 应该包含所有失败字段", async () => {
    const rules = {
      name: { required },
      email: { required, email },
    };
    const { errors, validate } = useFormValidation(rules, formData);

    await validate();

    expect(errors.value.name).toBeTruthy();
    expect(errors.value.email).toBeTruthy();
  });

  it("部分字段合法时 errors 只包含不合法字段", async () => {
    formData.name = "有效名称";
    const rules = {
      name: { required },
      email: { required, email },
    };
    const { errors, validate } = useFormValidation(rules, formData);

    await validate();

    expect(errors.value.name).toBeFalsy();
    expect(errors.value.email).toBeTruthy();
  });
});
