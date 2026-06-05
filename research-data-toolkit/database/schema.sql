-- MySQL schema for Research Data Processing & Automation Toolkit
CREATE DATABASE IF NOT EXISTS research_toolkit;
USE research_toolkit;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(128) NOT NULL,
    filename VARCHAR(256) NOT NULL,
    upload_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(32) NOT NULL DEFAULT 'Uploaded',
    rows INT DEFAULT 0,
    columns INT DEFAULT 0,
    summary JSON,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
