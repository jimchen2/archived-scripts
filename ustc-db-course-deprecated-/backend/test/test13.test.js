const request = require("supertest");
const initializeApp = require("../src/app");
const pool = require("../src/db");
describe("Test 13", () => {
  let app;
  let superadminToken;
  let teacherToken1;
  let teacherToken2;
  let projectId1;
  let projectId2; // Declare projectId2 here
  let teacherId2;

  beforeAll(async () => {
    try {
      app = await initializeApp();

      // Login as superadmin to get the token
      const superadminLoginResponse = await request(app)
        .post("/login")
        .send({ id: "-1", password: "password" });
      superadminToken = superadminLoginResponse.body.token;
    } catch (error) {
      console.error(
        "Failed to initialize the app or login as superadmin in beforeAll:",
        error
      );
      throw error;
    }
  });

  afterAll(async () => {
    // Close the database connection pool after the test is finished
    await pool.end();
  });

  it("should create 2 teachers, create 2 projects, and teacher 1 add themself to project 1", async () => {
    // Create project 1 using superadmin token
    // Create teacher 1
    const teacherData1 = {
      id: "3",
      name: "Jane Smith",
      gender: 2,
      title: 2,
      password: "password123",
    };
    const teacherResponse1 = await request(app)
      .post("/teachers")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(teacherData1);
    expect(teacherResponse1.status).toBe(201);
    teacherId1 = teacherResponse1.body.id;

    // Create teacher 2
    const teacherData2 = {
      id: "4",
      name: "Michael Johnson",
      gender: 1,
      title: 3,
      password: "password456",
    };
    const teacherResponse2 = await request(app)
      .post("/teachers")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(teacherData2);
    expect(teacherResponse2.status).toBe(201);
    teacherId2 = teacherResponse2.body.id;

    // Login as teacher

    const loginResponse1 = await request(app)
      .post("/login")
      .send({ id: 3, password: "password123" });
    expect(loginResponse1.status).toBe(200);
    teacherToken1 = loginResponse1.body.token;

    const projectData1 = {
      id: "P002",
      name: "Project 2",
      source: "Source 2",
      project_type: 2,
      total_funding: 8000,
      start_year: 2023,
      end_year: 2024,
    };
    const projectResponse1 = await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(projectData1);
    expect(projectResponse1.status).toBe(201);
    projectId1 = projectResponse1.body.id;

    const req1 = await request(app)
      .get("/projects")
      .set("Authorization", `Bearer ${superadminToken}`);
    console.log(req1.body);

    const projectData2 = {
      id: "P005",
      name: "Project 5",
      source: "Source 5",
      project_type: 2,
      total_funding: 7000,
      start_year: 2023,
      end_year: 2025,
    };
    const projectResponse2 = await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(projectData2);
    expect(projectResponse2.status).toBe(201);
    projectId2 = projectResponse2.body.id;
    const req2 = await request(app)
      .get("/projects")
      .set("Authorization", `Bearer ${superadminToken}`);
    console.log(req2.body);
  });
});
