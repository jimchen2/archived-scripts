-- CreateTable
CREATE TABLE `Teacher` (
    `id` CHAR(5) NOT NULL,
    `name` VARCHAR(256) NOT NULL,
    `gender` INTEGER NOT NULL,
    `title` INTEGER NOT NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `Paper` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(256) NOT NULL,
    `source` VARCHAR(256) NULL,
    `year` INTEGER NULL,
    `type` INTEGER NOT NULL,
    `level` INTEGER NOT NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `PublishedPaper` (
    `paper_id` INTEGER NOT NULL,
    `teacher_id` CHAR(5) NOT NULL,
    `ranking` INTEGER NOT NULL,
    `is_corresponding_author` BOOLEAN NOT NULL,

    UNIQUE INDEX `PublishedPaper_paper_id_ranking_key`(`paper_id`, `ranking`),
    PRIMARY KEY (`paper_id`, `teacher_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `Project` (
    `id` VARCHAR(256) NOT NULL,
    `name` VARCHAR(256) NOT NULL,
    `source` VARCHAR(256) NULL,
    `project_type` INTEGER NOT NULL,
    `total_funding` DOUBLE NULL,
    `start_year` INTEGER NULL,
    `end_year` INTEGER NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `ProjectParticipant` (
    `projectId` VARCHAR(256) NOT NULL,
    `teacher_id` CHAR(5) NOT NULL,
    `ranking` INTEGER NOT NULL,
    `funding` DOUBLE NULL,

    UNIQUE INDEX `ProjectParticipant_projectId_ranking_key`(`projectId`, `ranking`),
    PRIMARY KEY (`projectId`, `teacher_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `Course` (
    `id` VARCHAR(256) NOT NULL,
    `name` VARCHAR(256) NOT NULL,
    `total_hours` INTEGER NULL,
    `level` INTEGER NOT NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `TaughtCourse` (
    `course_id` VARCHAR(256) NOT NULL,
    `teacher_id` CHAR(5) NOT NULL,
    `year` INTEGER NULL,
    `term` INTEGER NOT NULL,
    `teaching_hours` INTEGER NULL,

    PRIMARY KEY (`course_id`, `teacher_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `PublishedPaper` ADD CONSTRAINT `PublishedPaper_paper_id_fkey` FOREIGN KEY (`paper_id`) REFERENCES `Paper`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `PublishedPaper` ADD CONSTRAINT `PublishedPaper_teacher_id_fkey` FOREIGN KEY (`teacher_id`) REFERENCES `Teacher`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `ProjectParticipant` ADD CONSTRAINT `ProjectParticipant_projectId_fkey` FOREIGN KEY (`projectId`) REFERENCES `Project`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `ProjectParticipant` ADD CONSTRAINT `ProjectParticipant_teacher_id_fkey` FOREIGN KEY (`teacher_id`) REFERENCES `Teacher`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `TaughtCourse` ADD CONSTRAINT `TaughtCourse_course_id_fkey` FOREIGN KEY (`course_id`) REFERENCES `Course`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `TaughtCourse` ADD CONSTRAINT `TaughtCourse_teacher_id_fkey` FOREIGN KEY (`teacher_id`) REFERENCES `Teacher`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;
