// test/authTests/test3.js
const request = require('supertest');
const initializeApp = require('../src/app');
const db = require('../src/db');
const jwt = require('jsonwebtoken');

describe('Test 3: Create a teacher and logging in with false password', () => {
  let app;
  let superadminToken;

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
    await db.query('DELETE FROM teacher_password WHERE teacher_id = ?', ['T0002']);
    await db.query('DELETE FROM teachers WHERE id = ?', ['T0002']);
    await db.end();
  });

  test('Create a teacher', async () => {
    const response = await request(app)
      .post('/teachers')
      .set('Authorization', `Bearer ${superadminToken}`)
      .send({
        id: '1',
        name: 'Jane Smith',
        gender: 2,
        title: 2,
        password: 'password456',
      });
    expect(response.status).toBe(201);
  });

  test('Log in with false password', async () => {
    const response = await request(app)
      .post('/login')
      .send({ id: 'T0002', password: 'wrongpassword' });
    expect(response.status).toBe(401);
  });
});