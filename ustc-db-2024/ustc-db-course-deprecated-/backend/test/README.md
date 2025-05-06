```
Test 1: Superadmin Log in
Test 2: Create a teacher and logging in as the teacher
Test 3: Create a teacher and logging in with false password(assume can't)
Test 4: Delete a teacher and try logging in again(assume can't)
Test 5: Test after Logging in a teacher is authorized(token), and test if an unauthorized teacher can get authenticated(false)
Test 6: Create duplicated teachers with the same ID(should return error)

Projects: (only Superadmin can create projects, teachers only add/remove themselves from projects)
Test 7: Create a teacher, create a project
Test 8: Create 3 projects, find one, list(should return 3)
Test 9: Create 3 projects, delete one, find the deleted(should error)
Test 10: Create 3 projects, change one, search(shall be changed)
Test 11: Create a teacher, create a project, teacher add themself to project
Test 12: Create a teacher, create 2 projects, teacher add themself to both
Test 13: Create 2 teachers, create 2 projects, teacher 1 add themself to project 1
```