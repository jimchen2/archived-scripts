// test/authTests/test2.js
const request = require('supertest');
const initializeApp = require('../src/app');
const db = require('../src/db');
const jwt = require('jsonwebtoken');

describe('Test 2: Create a teacher and logging in as the teacher', () => {
  let app;
  let superadminToken;
  let teacherToken;

  beforeAll(async () => {
    try {
      app = await initializeApp();
      const superadminLoginResponse = await request(app)
        .post('/login')
        .send({ id: '-1', password: 'password' });
      superadminToken = superadminLoginResponse.body.token;
    } catch (error) {
      console.error('Failed to initialize the app or log in as superadmin in beforeAll:', error);
      throw error;
    }
  });

  afterAll(async () => {
    await db.query('DELETE FROM teacher_password WHERE teacher_id = ?', ['T0001']);
    await db.query('DELETE FROM teachers WHERE id = ?', ['T0001']);
    await db.end();
  });

  test('Create a teacher', async () => {
    const response = await request(app)
      .post('/teachers')
      .set('Authorization', `Bearer ${superadminToken}`)
      .send({
        id: 'T0001',
        name: 'John Doe',
        gender: 1,
        title: 1,
        password: 'password123',
      });
    expect(response.status).toBe(201);
  });

  test('Log in as the teacher', async () => {
    const response = await request(app)
      .post('/login')
      .send({ id: 'T0001', password: 'password123' });
    expect(response.status).toBe(200);
    expect(response.body.token).toBeDefined();
    teacherToken = response.body.token;
  });
});