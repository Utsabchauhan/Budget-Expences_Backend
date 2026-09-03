-- Creates the dedicated BudgetFlow development schema.
-- Run as an Oracle admin user connected to the application PDB, for example:
-- sqlplus / as sysdba
-- ALTER SESSION SET CONTAINER = XEPDB1;
-- DEFINE BUDGETFLOW_PASSWORD = "replace_with_local_development_password"
-- @database/create_budgetflow_user.sql
--
-- Do not commit a real password. Provide it through SQL*Plus DEFINE or a
-- local-only environment/configuration value.

CREATE USER BUDGETFLOW IDENTIFIED BY "&BUDGETFLOW_PASSWORD";

GRANT CREATE SESSION TO BUDGETFLOW;
GRANT CREATE TABLE TO BUDGETFLOW;
GRANT CREATE SEQUENCE TO BUDGETFLOW;
GRANT CREATE VIEW TO BUDGETFLOW;
GRANT CREATE PROCEDURE TO BUDGETFLOW;

ALTER USER BUDGETFLOW QUOTA UNLIMITED ON USERS;
