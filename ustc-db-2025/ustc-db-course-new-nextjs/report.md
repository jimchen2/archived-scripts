PB21000002 陈加木

架构语言: Next.js, Prisma, Mysql

UI: Tailwind CSS

## **1. 需求分析**

- **1.1. 登记发表论文情况 (1.1)**

  - **1.1.1 增加论文信息：**
    - 输入字段：论文名称、发表刊物/会议名称、发表年份、论文类型（下拉框选择，如：期刊论文、会议论文、专著、专利等）、论文级别（下拉框选择，如：SCI 一区、SCI 二区、EI 会议、中文核心、普刊等）、所有作者信息（教师工号/姓名、排名、是否通讯作者）。
    - 校验规则：
      - 1.1.1.1 一篇论文只能有一位通讯作者。
      - 1.1.1.2 论文的作者排名不能有重复。
      - 1.1.1.3 论文类型和级别必须从预设集合中选择。
      - 1.1.1.4 必填项校验（如论文名称、年份、至少一位作者等）。
      - 1.1.1.5 作者工号需关联到预备数据中的教师信息。
  - **1.1.2 删除论文信息：**
    - 提供选择或搜索定位到特定论文记录，进行删除操作。
    - 删除前应有确认提示。
  - **1.1.3 修改论文信息：**
    - 提供选择或搜索定位到特定论文记录，对已有信息进行修改。
    - 修改时同样需要遵守 1.1.1 中的校验规则。
  - **1.1.4 查询论文信息：**
    - 支持按论文名称（模糊）、作者工号/姓名、发表年份、论文类型、论文级别等一个或多个条件组合查询。
    - 查询结果以列表形式展示，包含主要信息，并可查看详情。

- **1.2. 登记承担项目情况 (1.2)**

  - **1.2.1 增加项目信息：**
    - 输入字段：项目名称、项目编号（可选）、项目来源、项目类型（下拉框选择，如：国家级、省部级、市厅级、横向等）、项目总经费、立项年份、项目负责人、其他参与人信息（教师工号/姓名、排名、承担经费）。
    - 校验规则：
      - 1.2.1.1 项目参与人的排名不能有重复。
      - 1.2.1.2 一个项目中所有教师的承担经费总额应等于项目的总经费。
      - 1.2.1.3 项目类型必须从预设集合中选择。
      - 1.2.1.4 必填项校验（如项目名称、总经费、立项年份、负责人等）。
      - 1.2.1.5 参与教师工号需关联到预备数据中的教师信息。
  - **1.2.2 删除项目信息：**
    - 提供选择或搜索定位到特定项目记录，进行删除操作。
    - 删除前应有确认提示。
  - **1.2.3 修改项目信息：**
    - 提供选择或搜索定位到特定项目记录，对已有信息进行修改。
    - 修改时同样需要遵守 1.2.1 中的校验规则。
  - **1.2.4 查询项目信息：**
    - 支持按项目名称（模糊）、项目负责人、参与人、立项年份、项目类型等一个或多个条件组合查询。
    - 查询结果以列表形式展示，包含主要信息，并可查看详情。

- **1.3. 登记主讲课程情况 (1.3)**

  - **1.3.1 增加主讲课程信息：**
    - 输入字段：课程编号/名称（关联预备数据中的课程信息）、开课学期（如：2023-2024 第一学期）、主讲教师信息（教师工号/姓名、承担学时）。课程总学时应从预备课程信息中获取或允许输入。
    - 校验规则：
      - 1.3.1.1 一门课程在一个学期内，所有主讲教师的承担学时总额应等于该课程的总学时。
      - 1.3.1.2 学期格式应规范（如：YYYY-YYYY 第 X 学期，或通过年、学期下拉框组合）。
      - 1.3.1.3 必填项校验（如课程、学期、至少一位主讲教师等）。
      - 1.3.1.4 主讲教师工号需关联到预备数据中的教师信息。
      - 1.3.1.5 课程编号/名称需关联到预备数据中的课程信息。
  - **1.3.2 删除主讲课程信息：**
    - 提供选择或搜索定位到特定课程的教学安排记录，进行删除操作。
    - 删除前应有确认提示。
  - **1.3.3 修改主讲课程信息：**
    - 提供选择或搜索定位到特定课程的教学安排记录，对已有信息进行修改。
    - 修改时同样需要遵守 1.3.1 中的校验规则。
  - **1.3.4 查询主讲课程信息：**
    - 支持按课程名称/编号、主讲教师工号/姓名、开课学期等一个或多个条件组合查询。
    - 查询结果以列表形式展示，包含主要信息。

- **1.4. 查询统计 (1.4)**

  - **1.4.1 按教师汇总查询教学科研情况：**
    - 输入：教师工号、起始年份、结束年份。
    - 输出：指定教师在指定年份范围内：
      - 发表的论文列表（论文名称、刊物、年份、类型、级别、本人排名、是否通讯）。
      - 承担的项目列表（项目名称、类型、总经费、年份、本人排名、承担经费）。
      - 主讲的课程列表（课程名称、学期、本人承担学时、课程总学时）。
    - 结果应清晰展示，便于查看。
  - **1.4.2 教学科研工作量统计表导出 (1.4.2.Opt)：**

    - 基于 1.4.1 的查询结果。
    - 支持将查询结果按指定格式（见示例）导出为文档（PDF、Word、Excel 等）。
    - 示例格式：

      ```
      教学科研工作量统计表
      姓名: [教师姓名]   工号: [教师工号]   统计年份: [起始年份]-[结束年份]

      一、科研情况
      1. 论文：
         序号 | 论文名称 | 发表刊物/会议 | 发表年份 | 类型 | 级别 | 本人排名 | 是否通讯
         ---|----------|---------------|----------|------|------|----------|-----------
         ...| ...      | ...           | ...      | ...  | ...  | ...      | ...

      2. 项目：
         序号 | 项目名称 | 项目来源/类型 | 立项年份 | 总经费 | 本人排名 | 承担经费
         ---|----------|---------------|----------|--------|----------|-----------
         ...| ...      | ...           | ...      | ...    | ...      | ...

      二、教学情况
      1. 主讲课程：
         序号 | 课程名称 | 开课学期 | 课程总学时 | 本人承担学时
         ---|----------|----------|------------|-------------
         ...| ...      | ...      | ...        | ...
      ```

## **2. ER 图**

```
!pip install graphviz
!pip install graphviz
import graphviz

def generate_er_diagram(filename="prisma_er_diagram"):
    """
    Generates an ER diagram from the provided Prisma-like schema structure.
    """
    dot = graphviz.Digraph('ERD', comment='Prisma Schema ER Diagram')
    dot.attr(rankdir='LR') # Left to right layout
    dot.attr('node', shape='Mrecord', style='filled', fillcolor='lightblue') # Default node style

    # --- Define Entities (Nodes) ---
    # We'll use HTML-like labels for better formatting of attributes

    # Teacher
    dot.node('Teacher', '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                              <TR><TD COLSPAN="2" BGCOLOR="lightblue"><b>Teacher</b></TD></TR>
                              <TR><TD ALIGN="LEFT" PORT="id"><b>id (PK)</b></TD><TD ALIGN="LEFT">CHAR(5)</TD></TR>
                              <TR><TD ALIGN="LEFT">name</TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                              <TR><TD ALIGN="LEFT">gender</TD><TD ALIGN="LEFT">INT</TD></TR>
                              <TR><TD ALIGN="LEFT">title</TD><TD ALIGN="LEFT">INT</TD></TR>
                            </TABLE>>''', shape='none', margin='0')

    # Paper
    dot.node('Paper', '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                          <TR><TD COLSPAN="2" BGCOLOR="lightblue"><b>Paper</b></TD></TR>
                          <TR><TD ALIGN="LEFT" PORT="id"><b>id (PK)</b></TD><TD ALIGN="LEFT">INT (auto_increment)</TD></TR>
                          <TR><TD ALIGN="LEFT">name</TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                          <TR><TD ALIGN="LEFT">source</TD><TD ALIGN="LEFT">VARCHAR(256)?</TD></TR>
                          <TR><TD ALIGN="LEFT">year</TD><TD ALIGN="LEFT">INT?</TD></TR>
                          <TR><TD ALIGN="LEFT">type</TD><TD ALIGN="LEFT">INT</TD></TR>
                          <TR><TD ALIGN="LEFT">level</TD><TD ALIGN="LEFT">INT</TD></TR>
                        </TABLE>>''', shape='none', margin='0')

    # PublishedPaper (Linking Table)
    dot.node('PublishedPaper', '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                                <TR><TD COLSPAN="2" BGCOLOR="lightyellow"><b>PublishedPaper</b></TD></TR>
                                <TR><TD ALIGN="LEFT" PORT="paperId"><b>paper_id (FK, PK_part)</b></TD><TD ALIGN="LEFT">INT</TD></TR>
                                <TR><TD ALIGN="LEFT" PORT="teacherId"><b>teacher_id (FK, PK_part)</b></TD><TD ALIGN="LEFT">CHAR(5)</TD></TR>
                                <TR><TD ALIGN="LEFT">ranking</TD><TD ALIGN="LEFT">INT</TD></TR>
                                <TR><TD ALIGN="LEFT">is_corresponding_author</TD><TD ALIGN="LEFT">BOOLEAN</TD></TR>
                                <TR><TD ALIGN="LEFT" COLSPAN="2"><I>UNIQUE(paper_id, ranking)</I></TD></TR>
                              </TABLE>>''', shape='none', margin='0')

    # Project
    dot.node('Project', '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                            <TR><TD COLSPAN="2" BGCOLOR="lightblue"><b>Project</b></TD></TR>
                            <TR><TD ALIGN="LEFT" PORT="id"><b>id (PK)</b></TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                            <TR><TD ALIGN="LEFT">name</TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                            <TR><TD ALIGN="LEFT">source</TD><TD ALIGN="LEFT">VARCHAR(256)?</TD></TR>
                            <TR><TD ALIGN="LEFT">project_type</TD><TD ALIGN="LEFT">INT</TD></TR>
                            <TR><TD ALIGN="LEFT">total_funding</TD><TD ALIGN="LEFT">FLOAT?</TD></TR>
                            <TR><TD ALIGN="LEFT">start_year</TD><TD ALIGN="LEFT">INT?</TD></TR>
                            <TR><TD ALIGN="LEFT">end_year</TD><TD ALIGN="LEFT">INT?</TD></TR>
                            <TR><TD ALIGN="LEFT">project_file_url</TD><TD ALIGN="LEFT">STRING?</TD></TR>
                          </TABLE>>''', shape='none', margin='0')

    # ProjectParticipant (Linking Table)
    dot.node('ProjectParticipant', '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                                    <TR><TD COLSPAN="2" BGCOLOR="lightyellow"><b>ProjectParticipant</b></TD></TR>
                                    <TR><TD ALIGN="LEFT" PORT="projectId"><b>projectId (FK, PK_part)</b></TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                                    <TR><TD ALIGN="LEFT" PORT="teacherId"><b>teacher_id (FK, PK_part)</b></TD><TD ALIGN="LEFT">CHAR(5)</TD></TR>
                                    <TR><TD ALIGN="LEFT">ranking</TD><TD ALIGN="LEFT">INT</TD></TR>
                                    <TR><TD ALIGN="LEFT">funding</TD><TD ALIGN="LEFT">FLOAT?</TD></TR>
                                    <TR><TD ALIGN="LEFT" COLSPAN="2"><I>UNIQUE(projectId, ranking)</I></TD></TR>
                                  </TABLE>>''', shape='none', margin='0')

    # Course
    dot.node('Course', '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                          <TR><TD COLSPAN="2" BGCOLOR="lightblue"><b>Course</b></TD></TR>
                          <TR><TD ALIGN="LEFT" PORT="id"><b>id (PK)</b></TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                          <TR><TD ALIGN="LEFT">name</TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                          <TR><TD ALIGN="LEFT">total_hours</TD><TD ALIGN="LEFT">INT?</TD></TR>
                          <TR><TD ALIGN="LEFT">level</TD><TD ALIGN="LEFT">INT</TD></TR>
                        </TABLE>>''', shape='none', margin='0')

    # TaughtCourse (Linking Table)
    dot.node('TaughtCourse', '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                                <TR><TD COLSPAN="2" BGCOLOR="lightyellow"><b>TaughtCourse</b></TD></TR>
                                <TR><TD ALIGN="LEFT" PORT="courseId"><b>course_id (FK, PK_part)</b></TD><TD ALIGN="LEFT">VARCHAR(256)</TD></TR>
                                <TR><TD ALIGN="LEFT" PORT="teacherId"><b>teacher_id (FK, PK_part)</b></TD><TD ALIGN="LEFT">CHAR(5)</TD></TR>
                                <TR><TD ALIGN="LEFT"><b>year (PK_part)</b></TD><TD ALIGN="LEFT">INT</TD></TR>
                                <TR><TD ALIGN="LEFT"><b>term (PK_part)</b></TD><TD ALIGN="LEFT">INT</TD></TR>
                                <TR><TD ALIGN="LEFT">teaching_hours</TD><TD ALIGN="LEFT">INT?</TD></TR>
                              </TABLE>>''', shape='none', margin='0')


    # --- Define Relationships (Edges) ---
    # Using crow's foot notation for one-to-many.
    # Arrowhead 'crow' means "many", 'none' or 'tee' means "one".
    # 'odot' can mean "zero or one". We'll keep it simple with one/many.

    # Teacher <-> PublishedPaper <-> Paper (Many-to-Many via PublishedPaper)
    dot.edge('Teacher:id:e', 'PublishedPaper:teacherId:w', label='  has many', arrowhead='crow', arrowtail='none', dir='both')
    dot.edge('Paper:id:e', 'PublishedPaper:paperId:w', label='  published in', arrowhead='crow', arrowtail='none', dir='both')

    # Teacher <-> ProjectParticipant <-> Project (Many-to-Many via ProjectParticipant)
    dot.edge('Teacher:id:e', 'ProjectParticipant:teacherId:w', label='  participates in', arrowhead='crow', arrowtail='none', dir='both')
    dot.edge('Project:id:e', 'ProjectParticipant:projectId:w', label='  has participants', arrowhead='crow', arrowtail='none', dir='both')

    # Teacher <-> TaughtCourse <-> Course (Many-to-Many via TaughtCourse)
    dot.edge('Teacher:id:e', 'TaughtCourse:teacherId:w', label='  teaches', arrowhead='crow', arrowtail='none', dir='both')
    dot.edge('Course:id:e', 'TaughtCourse:courseId:w', label='  is taught in', arrowhead='crow', arrowtail='none', dir='both')

    # --- Render and Save ---
    # You can choose different formats like 'pdf', 'svg', etc.
    dot.render(filename, view=False, format='png') # Set view=True to auto-open
    print(f"ER diagram saved as {filename}.png and {filename}")

if __name__ == '__main__':
    generate_er_diagram()
```

![alt text](image-1.png)

## **3. 数据库设计和 3NF**

**核心实体表：**

1.  **`Teacher` (教师表)**: 存储教师基本信息 (工号 `id`, 姓名, 性别, 职称)。
2.  **`Paper` (论文表)**: 存储论文信息 (自增 `id`, 名称, 来源, 年份, 类型, 级别)。
3.  **`Project` (项目表)**: 存储项目信息 (项目编号 `id`, 名称, 来源, 类型, 经费, 起止年份, **最近新增了项目文件链接 `project_file_url`**)。
4.  **`Course` (课程表)**: 存储课程信息 (课程号 `id`, 名称, 总学时, 级别)。

**关系/连接表 (实现多对多关系)：**

5.  **`PublishedPaper` (发表论文表)**:
    - 连接 `Teacher` 和 `Paper`。
    - 记录某教师发表某论文的具体信息 (作者排名, 是否通讯作者)。
    - 主键: `(paperId, teacherId)`。
    - 唯一约束: `(paperId, ranking)` (同一论文排名唯一)。
6.  **`ProjectParticipant` (项目参与者表)**:
    - 连接 `Teacher` 和 `Project`。
    - 记录某教师参与某项目的具体信息 (排名, 分配经费)。
    - 主键: `(projectId, teacherId)`。
    - 唯一约束: `(projectId, ranking)` (同一项目排名唯一)。
7.  **`TaughtCourse` (授课表)**:
    - 连接 `Teacher` 和 `Course`。
    - 记录某教师在某学年学期讲授某课程的具体信息 (学年, 学期, 授课学时)。
    - **主键**: `(courseId, teacherId, year, term)`，使其能唯一标识一次授课活动。之前 `year` 字段是可选的，后改为必填。

这个数据库符合 3NF

1.  满足 1NF 和 2NF：数据原子化，有主键，且所有非主键属性都完全依赖于整个主键（对于复合主键表，如 `PublishedPaper`，其 `ranking` 依赖于 `paperId` 和 `teacherId` 两者）。
2.  无传递依赖：表中的非主键属性之间不存在依赖关系。例如，在 `Teacher` 表中，`name`, `gender`, `title` 都直接依赖于 `Teacher.id`，而 `gender` 并不决定 `title`。类似地，在 `Project` 表中，`projectType` 不会决定 `source`。连接表（如 `PublishedPaper`）中的属性（如 `ranking`）直接描述该“教师-论文”关系，依赖于联合主键。

## **4. 图片，视频，文件**

上传至 S3,返回链接

## **5. 存储过程，事务，触发器，函数**

### 5.1 存储过程

类似后端 API,整个 handler

```
user@fedora ~/D/u/p/api (master)> find .
.
./courses
./courses/create.ts
./courses/delete.ts
./courses/edit.ts
./courses/list.ts
./papers
./papers/create.ts
./papers/delete.ts
./papers/edit.ts
./papers/list.ts
./projects
./projects/create.ts
./projects/delete.ts
./projects/edit.ts
./projects/list.ts
./projects/upload.ts
./search
./search/search.ts
./teachers
./teachers/create.ts
./teachers/delete.ts
./teachers/edit.ts
./teachers/list.ts
user@fedora ~/D/u/p/api (master)>
```

### 5.2 事务: `await prisma.$transaction`

ACID

```
maxWait: 5000, 
timeout: 10000, 
isolationLevel: Prisma.TransactionIsolationLevel.Serializable, 
```

```
  $transaction<P extends Prisma.PrismaPromise<any>[]>(arg: [...P], options?: { isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<runtime.Types.Utils.UnwrapTuple<P>>

  $transaction<R>(fn: (prisma: Omit<PrismaClient, runtime.ITXClientDenyList>) => $Utils.JsPromise<R>, options?: { maxWait?: number, timeout?: number, isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<R>
```

```
user@fedora ~/D/u/p/api (master)> grep -r "await prisma.$transaction"
courses/create.ts:      const existingCourse = await prisma.course.findUnique({
courses/create.ts:      const existingTeachers = await prisma.teacher.findMany({
courses/create.ts:      const course = await prisma.course.create({
courses/delete.ts:      await prisma.taughtCourse.deleteMany({
courses/delete.ts:      await prisma.course.delete({
courses/edit.ts:      const existingTeachers = await prisma.teacher.findMany({
courses/edit.ts:      const course = await prisma.course.update({
courses/edit.ts:      await prisma.taughtCourse.deleteMany({
courses/edit.ts:      await prisma.taughtCourse.createMany({
courses/list.ts:        courses = await prisma.course.findMany({
courses/list.ts:        courses = await prisma.course.findMany({
papers/create.ts:      const existingTeachers = await prisma.teacher.findMany({
papers/create.ts:      const existingPaper = await prisma.paper.findFirst({
papers/create.ts:      const paper = await prisma.$transaction(async (tx) => {
papers/delete.ts:      await prisma.publishedPaper.deleteMany({
papers/delete.ts:      await prisma.paper.delete({
papers/edit.ts:      const existingTeachers = await prisma.teacher.findMany({
papers/edit.ts:      const paper = await prisma.paper.update({
papers/edit.ts:      await prisma.$transaction(async (tx) => {
papers/list.ts:        papers = await prisma.paper.findMany({
papers/list.ts:        papers = await prisma.paper.findMany({
projects/create.ts:      const existingTeachers = await prisma.teacher.findMany({
projects/create.ts:      const existingProject = await prisma.project.findFirst({
projects/create.ts:      const project = await prisma.$transaction(async (tx) => {
projects/delete.ts:      await prisma.projectParticipant.deleteMany({
projects/delete.ts:      await prisma.project.delete({
projects/edit.ts:      const existingTeachers = await prisma.teacher.findMany({
projects/edit.ts:      const project = await prisma.project.update({
projects/edit.ts:      await prisma.$transaction(async (tx) => {
projects/list.ts:        projects = await prisma.project.findMany({
projects/list.ts:        projects = await prisma.project.findMany({
search/search.ts:    const teacher = await prisma.teacher.findUnique({
teachers/create.ts:      const existingTeacher = await prisma.teacher.findFirst({
teachers/create.ts:      const teacher = await prisma.teacher.create({
teachers/delete.ts:      await prisma.publishedPaper.deleteMany({
teachers/delete.ts:      await prisma.projectParticipant.deleteMany({
teachers/delete.ts:      await prisma.taughtCourse.deleteMany({
teachers/delete.ts:      const teacher = await prisma.teacher.delete({
teachers/edit.ts:      const teacher = await prisma.teacher.update({
teachers/list.ts:        teachers = await prisma.teacher.findMany({
teachers/list.ts:        teachers = await prisma.teacher.findMany();
```

### 5.3 触发器

增加触发器

```sql
-- --------------------------------------------------------------------------------
-- Teacher Triggers
-- --------------------------------------------------------------------------------
DELIMITER $$
CREATE TRIGGER trg_teacher_id_length_insert
BEFORE INSERT ON Teacher
FOR EACH ROW
BEGIN
    IF CHAR_LENGTH(NEW.id) != 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Teacher ID must be exactly 5 characters long.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_teacher_id_length_update
BEFORE UPDATE ON Teacher
FOR EACH ROW
BEGIN
    IF CHAR_LENGTH(NEW.id) != 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Teacher ID must be exactly 5 characters long.';
    END IF;
END$$
DELIMITER ;

-- Trigger to prevent empty teacher names
DELIMITER $$
CREATE TRIGGER trg_teacher_name_not_empty_insert
BEFORE INSERT ON Teacher
FOR EACH ROW
BEGIN
    IF TRIM(NEW.name) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Teacher name cannot be empty.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_teacher_name_not_empty_update
BEFORE UPDATE ON Teacher
FOR EACH ROW
BEGIN
    IF TRIM(NEW.name) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Teacher name cannot be empty.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_teacher_gender_check_insert
BEFORE INSERT ON Teacher
FOR EACH ROW
BEGIN
    IF NEW.gender NOT IN (0, 1, 2) THEN -- Assuming 0, 1, 2 are valid
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid gender value for Teacher.';
    END IF;
END$$
DELIMITER ;


-- --------------------------------------------------------------------------------
-- Paper Triggers
-- --------------------------------------------------------------------------------

-- Trigger to ensure paper year is reasonable (e.g., not in the distant future or too far past)
DELIMITER $$
CREATE TRIGGER trg_paper_year_check_insert
BEFORE INSERT ON Paper
FOR EACH ROW
BEGIN
    IF NEW.year IS NOT NULL AND (NEW.year < 1900 OR NEW.year > YEAR(CURDATE()) + 5) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Paper year seems invalid.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_paper_year_check_update
BEFORE UPDATE ON Paper
FOR EACH ROW
BEGIN
    IF NEW.year IS NOT NULL AND (NEW.year < 1900 OR NEW.year > YEAR(CURDATE()) + 5) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Paper year seems invalid.';
    END IF;
END$$
DELIMITER ;


-- --------------------------------------------------------------------------------
-- PublishedPaper Triggers
-- --------------------------------------------------------------------------------

-- Trigger to ensure ranking is positive
DELIMITER $$
CREATE TRIGGER trg_published_paper_ranking_check_insert
BEFORE INSERT ON PublishedPaper
FOR EACH ROW
BEGIN
    IF NEW.ranking <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PublishedPaper ranking must be a positive integer.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_published_paper_ranking_check_update
BEFORE UPDATE ON PublishedPaper
FOR EACH ROW
BEGIN
    IF NEW.ranking <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PublishedPaper ranking must be a positive integer.';
    END IF;
END$$
DELIMITER ;


-- --------------------------------------------------------------------------------
-- Project Triggers
-- --------------------------------------------------------------------------------

-- Trigger to ensure project end_year is not before start_year
DELIMITER $$
CREATE TRIGGER trg_project_year_check_insert
BEFORE INSERT ON Project
FOR EACH ROW
BEGIN
    IF NEW.end_year IS NOT NULL AND NEW.start_year IS NOT NULL AND NEW.end_year < NEW.start_year THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project end_year cannot be before start_year.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_project_year_check_update
BEFORE UPDATE ON Project
FOR EACH ROW
BEGIN
    IF NEW.end_year IS NOT NULL AND NEW.start_year IS NOT NULL AND NEW.end_year < NEW.start_year THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project end_year cannot be before start_year.';
    END IF;
END$$
DELIMITER ;

-- Trigger to ensure project total_funding is not negative
DELIMITER $$
CREATE TRIGGER trg_project_funding_check_insert
BEFORE INSERT ON Project
FOR EACH ROW
BEGIN
    IF NEW.total_funding IS NOT NULL AND NEW.total_funding < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project total_funding cannot be negative.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_project_funding_check_update
BEFORE UPDATE ON Project
FOR EACH ROW
BEGIN
    IF NEW.total_funding IS NOT NULL AND NEW.total_funding < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project total_funding cannot be negative.';
    END IF;
END$$
DELIMITER ;


-- Trigger to ensure ProjectParticipant funding is not negative
DELIMITER $$
CREATE TRIGGER trg_project_participant_funding_check_insert
BEFORE INSERT ON ProjectParticipant
FOR EACH ROW
BEGIN
    IF NEW.funding IS NOT NULL AND NEW.funding < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ProjectParticipant funding cannot be negative.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_project_participant_funding_check_update
BEFORE UPDATE ON ProjectParticipant
FOR EACH ROW
BEGIN
    IF NEW.funding IS NOT NULL AND NEW.funding < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ProjectParticipant funding cannot be negative.';
    END IF;
END$$
DELIMITER ;


-- --------------------------------------------------------------------------------
-- Course Triggers
-- --------------------------------------------------------------------------------

-- Trigger to prevent empty course names
DELIMITER $$
CREATE TRIGGER trg_course_name_not_empty_insert
BEFORE INSERT ON Course
FOR EACH ROW
BEGIN
    IF TRIM(NEW.name) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course name cannot be empty.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_course_name_not_empty_update
BEFORE UPDATE ON Course
FOR EACH ROW
BEGIN
    IF TRIM(NEW.name) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course name cannot be empty.';
    END IF;
END$$
DELIMITER ;

-- Trigger to ensure total_hours is positive if provided
DELIMITER $$
CREATE TRIGGER trg_course_total_hours_check_insert
BEFORE INSERT ON Course
FOR EACH ROW
BEGIN
    IF NEW.total_hours IS NOT NULL AND NEW.total_hours <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course total_hours must be positive if specified.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_course_total_hours_check_update
BEFORE UPDATE ON Course
FOR EACH ROW
BEGIN
    IF NEW.total_hours IS NOT NULL AND NEW.total_hours <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course total_hours must be positive if specified.';
    END IF;
END$$
DELIMITER ;


-- --------------------------------------------------------------------------------
-- TaughtCourse Triggers
-- --------------------------------------------------------------------------------

-- Trigger to ensure teaching_hours is positive if provided
DELIMITER $$
CREATE TRIGGER trg_taught_course_hours_check_insert
BEFORE INSERT ON TaughtCourse
FOR EACH ROW
BEGIN
    IF NEW.teaching_hours IS NOT NULL AND NEW.teaching_hours <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TaughtCourse teaching_hours must be positive if specified.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_taught_course_hours_check_update
BEFORE UPDATE ON TaughtCourse
FOR EACH ROW
BEGIN
    IF NEW.teaching_hours IS NOT NULL AND NEW.teaching_hours <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TaughtCourse teaching_hours must be positive if specified.';
    END IF;
END$$
DELIMITER ;
```

加入触发器

```
SHOW TRIGGERS;
DROP TRIGGER trigger_name_to_delete;

SELECT TRIGGER_NAME FROM information_schema.TRIGGERS;
```

### 5.4 函数

类似后端的代码的函数

比如

```
const validateInput = (input: CourseInput): boolean => {
  return !!(input.id && input.name && input.totalHours !== undefined && input.level !== undefined && input.taughtCourses && Array.isArray(input.taughtCourses) && input.taughtCourses.length > 0);
};

// Check for duplicate course ID
const checkDuplicateCourse = async (id: string) => {
  const existingCourse = await prisma.course.findUnique({
    where: { id },
  });
  return existingCourse;
};

// Validate teachers' existence
const validateTeachers = async (taughtCourses: TaughtCourse[]): Promise<string | null> => {
  const teacherIds = taughtCourses.map((tc) => tc.teacherId);
  const existingTeachers = await prisma.teacher.findMany({
    where: { id: { in: teacherIds } },
    select: { id: true },
  });
  const existingTeacherIds = new Set(existingTeachers.map((t) => t.id));

  for (const teacherId of teacherIds) {
    if (!existingTeacherIds.has(teacherId)) {
      return teacherId;
    }
  }
  return null;
};
```

