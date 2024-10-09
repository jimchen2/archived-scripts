const request = require("supertest");
const initializeApp = require("../src/app");
const pool = require("../src/db");

describe("Test 12", () => {
  let app;
  let superadminToken;
  let teacherToken;
  let projectId1;
  let projectId2;
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

  it("should create a teacher, create 2 projects, and teacher add themself to both", async () => {
    // Create a teacher
    const teacherData = {
      id: "2",
      name: "John Doe",
      gender: 1,
      title: 1,
      password: "password789",
    };
    const teacherResponse = await request(app)
      .post("/teachers")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(teacherData);
    expect(teacherResponse.status).toBe(201);
    teacherId = teacherResponse.body.id;

    const response = await request(app)
      .post("/login")
      .send({ id: 2, password: "password789" });
    expect(response.status).toBe(200);
    teacherToken = response.body.token;

    // Create project 1 using superadmin token
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

    // Create project 2 using superadmin token
    const projectData2 = {
      id: "P003",
      name: "Project 3",
      source: "Source 3",
      project_type: 3,
      total_funding: 10000,
      start_year: 2023,
      end_year: 2025,
    };
    const projectResponse2 = await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(projectData2);
    expect(projectResponse2.status).toBe(201);
    projectId2 = projectResponse2.body.id;

    // Teacher add themself to project 1
    const participantData1 = {
      ranking: 1,
      funding: 3000,
    };
    const participantResponse1 = await request(app)
      .post(`/participants/${projectId1}`)
      .set("Authorization", `Bearer ${teacherToken}`)
      .send(participantData1);
    expect(participantResponse1.status).toBe(201);

    // Teacher add themself to project 2
    const participantData2 = {
      ranking: 2,
      funding: 4000,
    };
    const participantResponse2 = await request(app)
      .post(`/participants/${projectId2}`)
      .set("Authorization", `Bearer ${teacherToken}`)
      .send(participantData2);
    expect(participantResponse2.status).toBe(201);

    // Get teacher's participation in project 1
    const getParticipantsResponse1 = await request(app)
      .get(`/participants/${projectId1}`)
      .set("Authorization", `Bearer ${teacherToken}`);
    expect(getParticipantsResponse1.status).toBe(200);
    expect(getParticipantsResponse1.body).toEqual([
      {
        ranking: 1,
        funding: 3000,
      },
    ]);

    // Get teacher's participation in project 2
    const getParticipantsResponse2 = await request(app)
      .get(`/participants/${projectId2}`)
      .set("Authorization", `Bearer ${teacherToken}`);
    expect(getParticipantsResponse2.status).toBe(200);
    expect(getParticipantsResponse2.body).toEqual([
      {
        ranking: 2,
        funding: 4000,
      },
    ]);
  });
});