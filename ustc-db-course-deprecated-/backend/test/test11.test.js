const request = require("supertest");
const initializeApp = require("../src/app");
const pool = require("../src/db");

describe("Test 11", () => {
  let app;
  let superadminToken;
  let teacherToken;
  let projectId;
  let teacherId;

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

  it("should create a teacher, create a project, and teacher add themself to project", async () => {
    // Create a teacher
    const teacherData = {
      id: "1",
      name: "Jane Smith",
      gender: 2,
      title: 2,
      password: "password456",
    };
    const teacherResponse = await request(app)
      .post("/teachers")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(teacherData);
    expect(teacherResponse.status).toBe(201);
    teacherId = teacherResponse.body.id;

    const response = await request(app)
      .post("/login")
      .send({ id: 1, password: "password456" });
    expect(response.status).toBe(200);
    teacherToken = response.body.token;

    // Create a project using superadmin token
    const projectData = {
      id: "P001",
      name: "Project 1",
      source: "Source 1",
      project_type: 1,
      total_funding: 5000,
      start_year: 2022,
      end_year: 2023,
    };
    const projectResponse = await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(projectData);
    expect(projectResponse.status).toBe(201);
    projectId = projectResponse.body.id;

    // Teacher add themself to project
    const participantData = {
      ranking: 1,
      funding: 2000,
    };
    console.log("psaoifsaijd");
    console.log(projectId);
    console.log(teacherToken);
    const participantResponse = await request(app)
      .post(`/participants/${projectId}`)
      .set("Authorization", `Bearer ${teacherToken}`)
      .send(participantData);
    expect(participantResponse.status).toBe(201);

    const getParticipantsResponse = await request(app)
      .get(`/participants/${projectId}`)
      .set("Authorization", `Bearer ${teacherToken}`);
    expect(getParticipantsResponse.status).toBe(200);
    console.log(getParticipantsResponse.body);
    expect(getParticipantsResponse.body).toEqual([
      {
        ranking: 1,
        funding: 2000,
      },
    ]);
  });
});
