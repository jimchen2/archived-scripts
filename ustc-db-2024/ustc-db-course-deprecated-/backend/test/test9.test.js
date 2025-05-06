const request = require("supertest");
const initializeApp = require("../src/app");
const pool = require("../src/db");

describe("Test 9", () => {
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

  it("should create 3 projects, delete one, and return an error when finding the deleted project", async () => {
    // Create 3 projects
    const project1 = {
      id: "P001",
      name: "Project 1",
      source: "Source 1",
      project_type: 1,
      total_funding: 1000,
      start_year: 2022,
      end_year: 2023,
    };
    const project2 = {
      id: "P002",
      name: "Project 2",
      source: "Source 2",
      project_type: 2,
      total_funding: 2000,
      start_year: 2023,
      end_year: 2024,
    };
    const project3 = {
      id: "P003",
      name: "Project 3",
      source: "Source 3",
      project_type: 3,
      total_funding: 3000,
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

    // Delete one project
    await request(app)
      .delete("/projects/P002")
      .set("Authorization", `Bearer ${superadminToken}`);
    console.log("deleted");

    // Find the deleted project (should error)
    const findResponse = await request(app).get("/projects/P002");
    expect(findResponse.status).toBe(404);
    expect(findResponse.body).toEqual({});
  });
});
