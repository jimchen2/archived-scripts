// test/test7.js
const request = require("supertest");
const initializeApp = require("../src/app");
const db = require("../src/db");
const jwt = require("jsonwebtoken");

describe("Test 7: Create a teacher, create a project", () => {
  let app;
  let superadminToken;
  let teacherToken;
  let teacherId = "T0007";
  let teacherPassword = "password789";
  let projectId = "P0001";

  beforeAll(async () => {
    try {
      app = await initializeApp();
      const superadminLoginResponse = await request(app)
        .post("/login")
        .send({ id: "-1", password: "password" });
      superadminToken = superadminLoginResponse.body.token;
    } catch (error) {
      console.error(
        "Failed to initialize the app or log in as superadmin in beforeAll:",
        error
      );
      throw error;
    }
  });

  afterAll(async () => {
    // Close the database connection pool after all tests are finished
    await db.end();
  });

  test("Create a teacher", async () => {
    console.log("Creating a teacher");
    const response = await request(app)
      .post("/teachers")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send({
        id: teacherId,
        name: "John Smith",
        gender: 1,
        title: 3,
        password: teacherPassword,
      });
    expect(response.status).toBe(201);
    expect(response.body.id).toBe(teacherId);
  });

  test("Teacher can log in", async () => {
    console.log("Teacher logging in");
    const response = await request(app)
      .post("/login")
      .send({ id: teacherId, password: teacherPassword });
    expect(response.status).toBe(200);
    expect(response.body.token).toBeDefined();
    teacherToken = response.body.token;
  });

  test("Create a project", async () => {
    console.log("Creating a project");
    const response = await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send({
        id: projectId,
        name: "Research Project",
        source: "Funding Agency",
        project_type: 2,
        total_funding: 50000,
        start_year: 2023,
        end_year: 2025,
      });
    expect(response.status).toBe(201);
    expect(response.body.id).toBe(projectId);
  });
});
