/* 
SQL initialization script

Run: mysql -u rating -p -D rating_db < create_rating_db.sql

This will create user 'admin' with password 'password'.

*/

/* Drop all tables (cascade removes foreign keys also) */

DROP TABLE IF EXISTS background_question_answer;
DROP TABLE IF EXISTS background_question_option;
DROP TABLE IF EXISTS background_question;
DROP TABLE IF EXISTS forced_id;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS trial_randomization;
DROP TABLE IF EXISTS embody_answer;
DROP TABLE IF EXISTS embody_question;
DROP TABLE IF EXISTS answer;
DROP TABLE IF EXISTS answer_set;
DROP TABLE IF EXISTS question;
DROP TABLE IF EXISTS page;
DROP TABLE IF EXISTS experiment;

/* Experiment set */
CREATE TABLE experiment (
	idexperiment INTEGER NOT NULL AUTO_INCREMENT,
	name VARCHAR(120), 
	instruction TEXT, 
	directoryname VARCHAR(120), 
	language VARCHAR(120), 
	status VARCHAR(120), 
	randomization VARCHAR(120), 
	short_instruction TEXT, 
	single_sentence_instruction TEXT, 
	is_archived VARCHAR(120), 
	creator_name VARCHAR(120), 
	research_notification_filename VARCHAR(120), 
	creation_time DATETIME, 
	stimulus_size VARCHAR(120), 
	consent_text TEXT, 
	use_forced_id VARCHAR(120), 
	PRIMARY KEY (idexperiment)
);

/* Answer set holds session information about users experiment */
CREATE TABLE answer_set (
	idanswer_set INTEGER NOT NULL AUTO_INCREMENT, 
	experiment_idexperiment INTEGER, 
	session VARCHAR(120), 
	agreement VARCHAR(120), 
	answer_counter INTEGER, 
	registration_time DATETIME, 
	last_answer_time DATETIME, 
	PRIMARY KEY (idanswer_set), 
	FOREIGN KEY(experiment_idexperiment) REFERENCES experiment (idexperiment)
);

/* Background questions are asked before the experiment begins */ 
CREATE TABLE background_question (
	idbackground_question INTEGER NOT NULL AUTO_INCREMENT,
	background_question VARCHAR(120), 
	experiment_idexperiment INTEGER, 
	PRIMARY KEY (idbackground_question)
);
CREATE TABLE background_question_option (
	idbackground_question_option INTEGER NOT NULL AUTO_INCREMENT,
	background_question_idbackground_question INTEGER, 
	option VARCHAR(120), 
	PRIMARY KEY (idbackground_question_option), 
	FOREIGN KEY(background_question_idbackground_question) REFERENCES background_question (idbackground_question)
);
CREATE TABLE background_question_answer (
	idbackground_question_answer INTEGER NOT NULL AUTO_INCREMENT,
	answer_set_idanswer_set INTEGER, 
	answer VARCHAR(120), 
	background_question_idbackground_question INTEGER, 
	PRIMARY KEY (idbackground_question_answer), 
	FOREIGN KEY(answer_set_idanswer_set) REFERENCES answer_set (idanswer_set), 
	FOREIGN KEY(background_question_idbackground_question) REFERENCES background_question (idbackground_question)
);

/* Randomize experiment page order  */
CREATE TABLE trial_randomization (
	idtrial_randomization INTEGER NOT NULL AUTO_INCREMENT, 
	page_idpage INTEGER, 
	randomized_idpage INTEGER, 
	answer_set_idanswer_set INTEGER, 
	experiment_idexperiment INTEGER, 
	PRIMARY KEY (idtrial_randomization)
);

CREATE TABLE user (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(64), 
	email VARCHAR(120), 
	password_hash VARCHAR(128), 
	PRIMARY KEY (id)
);

/* By using forced ID login subjects can only participate to a rating task by logging in with a pregenerated ID */
CREATE TABLE forced_id (
	idforced_id INTEGER NOT NULL AUTO_INCREMENT,
	experiment_idexperiment INTEGER, 
	pregenerated_id VARCHAR(120), 
	PRIMARY KEY (idforced_id), 
	FOREIGN KEY(experiment_idexperiment) REFERENCES experiment (idexperiment)
);

/* Information about stimulus type and content on a page */
CREATE TABLE page (
	idpage INTEGER NOT NULL AUTO_INCREMENT,
	experiment_idexperiment INTEGER, 
	type VARCHAR(120), 
	text VARCHAR(120), 
	media VARCHAR(120), 
	PRIMARY KEY (idpage), 
	FOREIGN KEY(experiment_idexperiment) REFERENCES experiment (idexperiment)
);

/* Slider question */
CREATE TABLE question (
	idquestion INTEGER NOT NULL AUTO_INCREMENT,
	experiment_idexperiment INTEGER, 
	question VARCHAR(120), 
	`left` VARCHAR(120), 
	`right` VARCHAR(120), 
	PRIMARY KEY (idquestion), 
	FOREIGN KEY(experiment_idexperiment) REFERENCES experiment (idexperiment)
);

/* Slider answer */
CREATE TABLE answer (
	idanswer INTEGER NOT NULL AUTO_INCREMENT,
	question_idquestion INTEGER, 
	answer_set_idanswer_set INTEGER, 
	answer VARCHAR(120), 
	page_idpage INTEGER, 
	PRIMARY KEY (idanswer), 
	FOREIGN KEY(answer_set_idanswer_set) REFERENCES answer_set (idanswer_set), 
	FOREIGN KEY(page_idpage) REFERENCES page (idpage), 
	FOREIGN KEY(question_idquestion) REFERENCES question (idquestion)
);

/* Create indexes for faster operations */
CREATE INDEX ix_experiment_consent_text ON experiment (consent_text(255));
CREATE INDEX ix_experiment_creation_time ON experiment (creation_time);
CREATE UNIQUE INDEX ix_experiment_directoryname ON experiment (directoryname);
CREATE INDEX ix_experiment_instruction ON experiment (instruction(255));
CREATE INDEX ix_experiment_name ON experiment (name);
CREATE INDEX ix_experiment_short_instruction ON experiment (short_instruction(255));
CREATE INDEX ix_experiment_single_sentence_instruction ON experiment (single_sentence_instruction(255));
CREATE UNIQUE INDEX ix_user_email ON user (email);
CREATE UNIQUE INDEX ix_user_username ON user (username);
CREATE INDEX ix_answer_set_last_answer_time ON answer_set (last_answer_time);
CREATE INDEX ix_answer_set_registration_time ON answer_set (registration_time);
CREATE INDEX ix_page_media ON page (media);
CREATE INDEX ix_page_text ON page (text);
CREATE INDEX ix_page_type ON page (type);


/* New fields for updating embody tool to onni.utu.fi */

/* Embody picture/question information */
CREATE TABLE embody_question (
	idembody INTEGER NOT NULL AUTO_INCREMENT,
	experiment_idexperiment INTEGER, 
	picture TEXT, 
	question TEXT, 
	PRIMARY KEY (idembody), 
	FOREIGN KEY(experiment_idexperiment) REFERENCES experiment (idexperiment)
);

/* Embody answer (coordinates). Answer is saved as a json object: 
	{x:[1,2,100,..], y:[3,4,101,..], r:[13,13,8,...]} */
CREATE TABLE embody_answer (
	idanswer INTEGER NOT NULL AUTO_INCREMENT,
	answer_set_idanswer_set INTEGER, 
	page_idpage INTEGER, 
    embody_question_idembody INTEGER DEFAULT 0,
	coordinates TEXT, 
	PRIMARY KEY (idanswer), 
	FOREIGN KEY(answer_set_idanswer_set) REFERENCES answer_set (idanswer_set), 
	FOREIGN KEY(page_idpage) REFERENCES page (idpage) ,
	FOREIGN KEY(embody_question_idembody) REFERENCES embody_question (idembody) 
);


/* Set flag if embody tool is enabled -> this is not the most modular solution, but works for now */
ALTER TABLE experiment ADD COLUMN (embody_enabled BOOLEAN DEFAULT 0);

/* Set current answer type (embody/slider/etc..) so returning users are routed to correct question */ 
ALTER TABLE answer_set ADD COLUMN (answer_type VARCHAR(120));

INSERT INTO user VALUES(1,'admin',NULL,'pbkdf2:sha256:50000$6Cc6Mjmo$3fe413a88db1bacfc4d617f7c1547bd1ea4cbd6c5d675a58e78332201f6befc6');

/* eyelabs */
INSERT INTO user VALUES(1,'eyelabs',NULL,'pbkdf2:sha256:50000$sdBu3Rjm$7ab97c6d2686460b85a2a20517b7012c15ffb341ba3fef5b0f17ed8354fc38d9');


CREATE TABLE research_group (
	id INTEGER NOT NULL AUTO_INCREMENT,
	name TEXT, 
	tag TEXT, 
	description TEXT,
	PRIMARY KEY (id)
);

INSERT INTO research_group(id, name, tag, description) VALUES(1, 'Human Emotion Systems', 'emotion', 'Welcome to the Human Emotion Systems -laboratory`s Onni-net laboratory! The experiments that are currently underway are listed below - you can participate for as many experiments you want.');
INSERT INTO research_group(id, name, tag, description) VALUES(2, 'Turku Eye-tracking', 'eyelabs', 'Welcome to the Turku Eyelabs -laboratory`s Onni-net laboratory! The experiments that are currently underway are listed below - you can participate for as many experiments you want.');

CREATE TABLE user_in_group (
	idgroup INTEGER,
	iduser INTEGER,
	role TEXT,
	FOREIGN KEY(idgroup) REFERENCES research_group (id), 
	FOREIGN KEY(iduser) REFERENCES user (id)
);

INSERT INTO user_in_group VALUES (1,1);
INSERT INTO user_in_group VALUES (2,1);

ALTER TABLE experiment ADD COLUMN (group_id INTEGER), ADD FOREIGN KEY(group_id) REFERENCES research_group(id);

