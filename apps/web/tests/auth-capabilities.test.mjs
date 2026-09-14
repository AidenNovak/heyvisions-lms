import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import {
  getAuthCapabilities,
  isGoogleSignInConfigured,
  isTransactionalEmailConfigured,
} from "../services/auth/authCapabilities.ts";

/**
 * 这些断言锁的是「没配就不算可用」这条线。
 *
 * 曾经的缺陷是：组织策略把 google / magic_login 都开着，环境里却没凭据，
 * 于是入口照摆 —— Google 点下去 500，邮件入口则谎报「已发送」。
 * 所以这里必须断言「缺凭据 ⇒ false」，而不是只看「设了 ⇒ true」。
 */

const KEYS = ["RESEND_API_KEY", "LEARNHOUSE_GOOGLE_CLIENT_ID"];

let saved;

beforeEach(() => {
  saved = KEYS.map((k) => [k, process.env[k]]);
  for (const k of KEYS) delete process.env[k];
});

afterEach(() => {
  for (const [k, v] of saved) {
    if (v === undefined) delete process.env[k];
    else process.env[k] = v;
  }
});

describe("authCapabilities", () => {
  test("什么都没配时，两项都不可用（当前生产就是这种形态）", () => {
    expect(isTransactionalEmailConfigured()).toBe(false);
    expect(isGoogleSignInConfigured()).toBe(false);
    expect(getAuthCapabilities()).toEqual({ email: false, google: false });
  });

  test("空字符串不算配好 —— 空 key 发不出信，也换不到 token", () => {
    process.env.RESEND_API_KEY = "";
    process.env.LEARNHOUSE_GOOGLE_CLIENT_ID = "";
    expect(getAuthCapabilities()).toEqual({ email: false, google: false });
  });

  test("只配发信 ⇒ 只有邮件可用，Google 仍不摆出来", () => {
    process.env.RESEND_API_KEY = "re_test_key";
    expect(getAuthCapabilities()).toEqual({ email: true, google: false });
  });

  test("只配 Google ⇒ 只有 Google 可用", () => {
    process.env.LEARNHOUSE_GOOGLE_CLIENT_ID = "test-client-id.apps.googleusercontent.com";
    expect(getAuthCapabilities()).toEqual({ email: false, google: true });
  });

  test("两项都配好 ⇒ 都可用", () => {
    process.env.RESEND_API_KEY = "re_test_key";
    process.env.LEARNHOUSE_GOOGLE_CLIENT_ID = "test-client-id.apps.googleusercontent.com";
    expect(getAuthCapabilities()).toEqual({ email: true, google: true });
  });

  test("每次调用都重新读环境 —— 不缓存，改配置无需重启进程才对", () => {
    expect(isTransactionalEmailConfigured()).toBe(false);
    process.env.RESEND_API_KEY = "re_test_key";
    expect(isTransactionalEmailConfigured()).toBe(true);
    delete process.env.RESEND_API_KEY;
    expect(isTransactionalEmailConfigured()).toBe(false);
  });
});
