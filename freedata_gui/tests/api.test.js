import { expect, test } from "vitest";
import { buildURL } from "../src/js/api";

test("builds URLs correctly"),
  () => {
    const params = { host: "127.0.0.1", port: 123 };
    expect(buildURL(params, "/config")).toBe("http://127.0.0.1/config");
  };
