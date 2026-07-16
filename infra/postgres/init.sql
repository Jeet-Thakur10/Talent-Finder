-- Initialisation script executed once by the official postgres Docker image
-- when the data volume is empty (first boot only).
-- Creates the two logical databases required by the application.

CREATE DATABASE usecase;
CREATE DATABASE sourcing;
