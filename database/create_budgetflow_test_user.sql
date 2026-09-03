-- Creates the dedicated BudgetFlow automated-test schema.
-- Run as an Oracle admin user connected to the application PDB, for example:
-- sqlplus / as sysdba
-- ALTER SESSION SET CONTAINER = XEPDB1;
-- DEFINE BUDGETFLOW_TEST_PASSWORD = "replace_with_local_test_password"
-- @database/create_budgetflow_test_user.sql
--
-- Do not commit a real password. Store the same value only in .env as
-- ORACLE_TEST_PASSWORD.

CREATE USER BUDGETFLOW_TEST IDENTIFIED BY "&BUDGETFLOW_TEST_PASSWORD";

GRANT CREATE SESSION TO BUDGETFLOW_TEST;
GRANT CREATE TABLE TO BUDGETFLOW_TEST;
GRANT CREATE SEQUENCE TO BUDGETFLOW_TEST;
GRANT CREATE PROCEDURE TO BUDGETFLOW_TEST;
GRANT CREATE TRIGGER TO BUDGETFLOW_TEST;
GRANT CREATE VIEW TO BUDGETFLOW_TEST;

ALTER USER BUDGETFLOW_TEST QUOTA UNLIMITED ON USERS;
