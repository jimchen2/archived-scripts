// test/authTests/test5.js
const request = require("supertest");
const initializeApp = require("../src/app");
const db = require("../src/db");
const jwt = require("jsonwebtoken");

describe("Test 5: Test after Logging in a teacher is authorized, and test if an unauthorized teacher can log in", () => {
  let app;
  let superadminToken;
  let teacherId = "T0004";
  let teacherPassword = "password123";

  beforeAll(async () => {
    try {
      app = await initializeApp();
      const superadminLoginResponse = await request(app)
        .post("/login")
        .send({ id: "-1", password: "password" });
      superadminToken = superadminLoginResponse.body.token;

      console.log("superadmin Logged in");
      await request(app)
        .post("/teachers")
        .set("Authorization", `Bearer ${superadminToken}`)
        .send({
          id: teacherId,
          name: "Emily Davis",
          gender: 2,
          title: 4,
          password: teacherPassword,
        });
    } catch (error) {
      console.error(
        "Failed to initialize the app, log in as superadmin, or create teacher in beforeAll:",
        error
      );
      throw error;
    }
  });

  afterAll(async () => {
    await db.query("DELETE FROM teacher_password WHERE teacher_id = ?", [
      teacherId,
    ]);
    await db.query("DELETE FROM teachers WHERE id = ?", [teacherId]);
    await db.end();
  });

  test("Authorized teacher can log in", async () => {
    const response = await request(app)
      .post("/login")
      .send({ id: teacherId, password: teacherPassword });
    expect(response.status).toBe(200);
    expect(response.body.token).toBeDefined();
  });

  test("Unauthorized teacher cannot log in", async () => {
    const response = await request(app)
      .post("/login")
      .send({ id: teacherId, password: "wrongpassword" });
    expect(response.status).toBe(401);
  });
});
