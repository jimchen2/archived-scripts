/*
  Warnings:

  - The primary key for the `TaughtCourse` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - Made the column `year` on table `TaughtCourse` required. This step will fail if there are existing NULL values in that column.

*/
-- AlterTable
ALTER TABLE `TaughtCourse` DROP PRIMARY KEY,
    MODIFY `year` INTEGER NOT NULL,
    ADD PRIMARY KEY (`course_id`, `teacher_id`, `year`, `term`);
