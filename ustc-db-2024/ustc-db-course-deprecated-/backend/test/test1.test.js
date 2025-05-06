// test/authTests/test1.js
const request = require("supertest");
const initializeApp = require("../src/app");
const db = require("../src/db");
const jwt = require("jsonwebtoken");

describe("Test 1: Superadmin Log in", () => {
  let app;

  beforeAll(async () => {
    try {
      app = await initializeApp();
    } catch (error) {
      console.error("Failed to initialize the app in beforeAll:", error);
      throw error;
    }
  });

  afterAll(async () => {
    await db.end();
  });

  test("Superadmin Log in", async () => {
    const response = await request(app)
      .post("/login")
      .send({ id: "-1", password: "password" });
    expect(response.status).toBe(200);
    expect(response.body.token).toBeDefined();
  });
});
