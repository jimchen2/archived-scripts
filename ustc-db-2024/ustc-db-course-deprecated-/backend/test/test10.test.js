const request = require("supertest");
const initializeApp = require("../src/app");
const pool = require("../src/db");

describe("Test 10", () => {
  let app;
  let superadminToken;

  beforeAll(async () => {
    try {
      app = await initializeApp();
      const superadminLoginResponse = await request(app)
        .post("/login")
        .send({ id: "-1", password: "password" });
      superadminToken = superadminLoginResponse.body.token;

      // Clear the projects table before running the test
      await pool.query("DELETE FROM projects");
    } catch (error) {
      console.error(
        "Failed to initialize the app or log in as superadmin in beforeAll:",
        error
      );
      throw error;
    }
  });

  afterAll(async () => {
    // Close the database connection pool after the test is finished
    await pool.end();
  });

  it("should create 3 projects, change one, and search for the changed project", async () => {
    // Create 3 projects
    const project1 = {
      id: "P004",
      name: "Project 4",
      source: "Source 4",
      project_type: 1,
      total_funding: 4000,
      start_year: 2022,
      end_year: 2023,
    };
    const project2 = {
      id: "P005",
      name: "Project 5",
      source: "Source 5",
      project_type: 2,
      total_funding: 5000,
      start_year: 2023,
      end_year: 2024,
    };
    const project3 = {
      id: "P006",
      name: "Project 6",
      source: "Source 6",
      project_type: 3,
      total_funding: 6000,
      start_year: 2024,
      end_year: 2025,
    };

    await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(project1);
    await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(project2);
    await request(app)
      .post("/projects")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(project3);

    // Change one project
    const updatedProject = {
      name: "Updated Project 5",
      source: "Updated Source 5",
      project_type: 4,
      total_funding: 10000,
      start_year: 2023,
      end_year: 2025,
    };
    await request(app)
      .put("/projects/P005")
      .set("Authorization", `Bearer ${superadminToken}`)
      .send(updatedProject);

    // Search for the changed project
    const searchResponse = await request(app).get("/projects/P005");
    expect(searchResponse.status).toBe(200);
    expect(searchResponse.body[0]).toEqual({
      id: "P005",
      ...updatedProject,
    });
  });
});
