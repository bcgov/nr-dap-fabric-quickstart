-- Create the schema only if it does not already exist
IF SCHEMA_ID(N'erp_replication') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA [erp_replication] AUTHORIZATION [dbo]');
END;
GO
