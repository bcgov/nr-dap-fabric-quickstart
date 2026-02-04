-- Create the schema only if it does not already exist
IF SCHEMA_ID(N'erp_reporting') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA [erp_reporting] AUTHORIZATION [dbo]');
END;
GO
