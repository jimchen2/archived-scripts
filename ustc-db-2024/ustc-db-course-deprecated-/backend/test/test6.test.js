// test/authTests/test6.js
const request = require('supertest');
const initializeApp = require('../src/app');
const db = require('../src/db');
const jwt = require('jsonwebtoken');

describe('Test 6: Create duplicated teachers with the same ID (should return error)', () => {
  let app;
  let superadminToken;

  beforeAll(async () => {
    try {
      app = await initializeApp();
      const superadminLoginResponse = await request(app)
        .post('/login')
        .send({ id: '-1', password: 'password' });
      superadminToken = superadminLoginResponse.body.token;

      await request(app)
        .post('/teachers')
        .set('Authorization', `Bearer ${superadminToken}`)
        .send({
          id: '1',
          name: 'John Doe',
          gender: 1,
          title: 2,
          password: 'password456',
        });
    } catch (error) {
      console.error('Failed to initialize the app, log in as superadmin, or create teacher in beforeAll:', error);
      throw error;
    }
  });

  afterAll(async () => {
    await db.query('DELETE FROM teacher_password WHERE teacher_id = ?', ['T0005']);
    await db.query('DELETE FROM teachers WHERE id = ?', ['T0005']);
    await db.end();
  });

  test('Create a teacher with a duplicate ID', async () => {
    const response = await request(app)
      .post('/teachers')
      .set('Authorization', `Bearer ${superadminToken}`)
      .send({
        id: '1',
        name: 'Jane Smith',
        gender: 2,
        title: 3,
        password: 'password789',
      });

    expect(response.status).toBe(409);
    expect(response.text).toBe('Teacher with this ID already exists');
  });
});