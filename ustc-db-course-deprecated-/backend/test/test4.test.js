// test/authTests/test4.js
const request = require('supertest');
const initializeApp = require('../src/app');
const db = require('../src/db');
const jwt = require('jsonwebtoken');

describe('Test 4: Delete a teacher and try logging in again', () => {
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
          name: 'Michael Johnson',
          gender: 1,
          title: 3,
          password: 'password789',
        });
    } catch (error) {
      console.error('Failed to initialize the app, log in as superadmin, or create teacher in beforeAll:', error);
      throw error;
    }
  });

  afterAll(async () => {
    await db.query('DELETE FROM teacher_password WHERE teacher_id = ?', ['T0003']);
    await db.query('DELETE FROM teachers WHERE id = ?', ['T0003']);
    await db.end();
  });

  test('Delete the teacher', async () => {
    const response = await request(app)
      .delete('/teachers/T0003')
      .set('Authorization', `Bearer ${superadminToken}`);
    expect(response.status).toBe(200);
  });

  test('Log in after deletion', async () => {
    const response = await request(app)
      .post('/login')
      .send({ id: 'T0003', password: 'password789' });
    expect(response.status).toBe(401);
  });
});