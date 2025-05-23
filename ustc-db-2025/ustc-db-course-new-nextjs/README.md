```
sudo fallocate -l "2G" /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile swap swap defaults 0 0" | sudo tee -a /etc/fstab

sudo apt update && sudo apt upgrade -y
sudo apt install git build-essential npm nginx certbot gnupg curl screen mariadb-server -y

curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
sudo apt install nodejs -y

sudo useradd -m builduser
sudo passwd -d builduser
echo 'builduser ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/builduser

sudo systemctl enable --now mariadb
```
##################################################################
```
sudo mkdir -p /var/www; sudo git clone https://github.com/jimchen2/ustc-db-course-new-nextjs /var/www/Website; sudo chown -R builduser:builduser /var/www/Website

# Configure password for database

# mysql -u root -p -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' IDENTIFIED BY 'your_root_password'; FLUSH PRIVILEGES;"

sudo -u builduser bash -c 'cd /var/www/Website; npm install;npx prisma migrate dev --name init;npm run build;'

sudo systemctl stop nginx
sudo systemctl stop ufw
sudo certbot certonly --standalone -d jimchen.uk --email jimchen4214@gmail.com --non-interactive --agree-tos
sudo systemctl start ufw

mkdir -p /etc/nginx/{sites-available,sites-enabled} && sudo ln -sf /etc/nginx/sites-available/website.conf /etc/nginx/sites-enabled/
sudo cp /var/www/Website/website.conf /etc/nginx/sites-available/website.conf
sudo cp /var/www/Website/nginx.conf /etc/nginx/nginx.conf
sudo systemctl enable --now nginx

sudo cp /var/www/Website/website.service /etc/systemd/system/website.service
sudo cp /var/www/Website/update-website.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now website.service
```

```
CREATE DATABASE my_nextjs_db;
```



```
-- Use database column names (e.g., start_year, end_year)
DELIMITER //
CREATE TRIGGER trg_project_check_dates_before_insert
BEFORE INSERT ON `Project`
FOR EACH ROW
BEGIN
    IF NEW.start_year IS NOT NULL AND NEW.end_year IS NOT NULL AND NEW.end_year < NEW.start_year THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project end_year cannot be before start_year.';
    END IF;
END;
//
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_project_check_dates_before_update
BEFORE UPDATE ON `Project`
FOR EACH ROW
BEGIN
    IF NEW.start_year IS NOT NULL AND NEW.end_year IS NOT NULL AND NEW.end_year < NEW.start_year THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project end_year cannot be before start_year.';
    END IF;
END;
//
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_published_paper_prevent_last_corresponding_author_update
BEFORE UPDATE ON `PublishedPaper`
FOR EACH ROW
BEGIN
    DECLARE corresponding_authors_count INT;
    -- Check if 'is_corresponding_author' is being changed from TRUE to FALSE
    IF OLD.is_corresponding_author = TRUE AND NEW.is_corresponding_author = FALSE THEN
        -- Count other corresponding authors for the same paper
        SELECT COUNT(*) INTO corresponding_authors_count
        FROM `PublishedPaper`
        WHERE paper_id = OLD.paper_id AND is_corresponding_author = TRUE AND teacher_id != OLD.teacher_id;

        IF corresponding_authors_count = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot change status for the last corresponding author. Assign another first or ensure this remains corresponding.';
        END IF;
    END IF;
END;
//
DELIMITER ;

-- Use database column names (e.g., project_id, total_funding)
DELIMITER //
CREATE TRIGGER trg_project_participant_check_funding_after_insert_update
AFTER INSERT ON `ProjectParticipant`
FOR EACH ROW
BEGIN
    DECLARE current_total_participant_funding FLOAT;
    DECLARE project_total_funding FLOAT;

    SELECT SUM(pp.funding) INTO current_total_participant_funding
    FROM `ProjectParticipant` pp
    WHERE pp.project_id = NEW.project_id;

    SELECT p.total_funding INTO project_total_funding
    FROM `Project` p
    WHERE p.id = NEW.project_id;

    IF current_total_participant_funding IS NOT NULL AND project_total_funding IS NOT NULL AND current_total_participant_funding > project_total_funding THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Total participant funding exceeds project total funding.';
    END IF;
END;
//
DELIMITER ;

-- Also need for UPDATE on ProjectParticipant
DELIMITER //
CREATE TRIGGER trg_project_participant_check_funding_after_update -- Renamed from the above for clarity
AFTER UPDATE ON `ProjectParticipant`
FOR EACH ROW
BEGIN
    DECLARE current_total_participant_funding FLOAT;
    DECLARE project_total_funding FLOAT;

    -- Only re-check if funding or project_id changed
    IF NEW.funding <> OLD.funding OR NEW.project_id <> OLD.project_id THEN
        SELECT SUM(pp.funding) INTO current_total_participant_funding
        FROM `ProjectParticipant` pp
        WHERE pp.project_id = NEW.project_id;

        SELECT p.total_funding INTO project_total_funding
        FROM `Project` p
        WHERE p.id = NEW.project_id;

        IF current_total_participant_funding IS NOT NULL AND project_total_funding IS NOT NULL AND current_total_participant_funding > project_total_funding THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Total participant funding exceeds project total funding.';
        END IF;
    END IF;
END;
//
DELIMITER ;


-- Trigger on Project update (if total_funding is reduced)
DELIMITER //
CREATE TRIGGER trg_project_check_funding_after_update
AFTER UPDATE ON `Project`
FOR EACH ROW
BEGIN
    DECLARE current_total_participant_funding FLOAT;

    -- Only check if total_funding was actually reduced
    IF NEW.total_funding < OLD.total_funding THEN
        SELECT SUM(pp.funding) INTO current_total_participant_funding
        FROM `ProjectParticipant` pp
        WHERE pp.project_id = NEW.id;

        IF current_total_participant_funding IS NOT NULL AND NEW.total_funding IS NOT NULL AND current_total_participant_funding > NEW.total_funding THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Reducing project total funding makes participant funding invalid.';
        END IF;
    END IF;
END;
//
DELIMITER ;
```