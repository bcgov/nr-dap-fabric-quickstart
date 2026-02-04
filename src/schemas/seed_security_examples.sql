-- Starter security scaffolding (adjust to your Warehouse)
-- Role for read access to reporting schema
CREATE ROLE reporting_readers;
GO

-- Example: Column-level GRANT on curated table (hide email column)
-- Table: erp_reporting.customers_curated (id, name, age, country, email, signup_date)
GRANT SELECT (id, name, age, country, signup_date)
ON OBJECT::erp_reporting.customers_curated TO reporting_readers;
GO

-- (Optional) Row-Level Security skeleton
-- CREATE FUNCTION dbo.fn_rls_allow_user(@user_name sysname)
-- RETURNS TABLE AS RETURN SELECT 1 AS allow WHERE @user_name = USER_NAME();
-- GO
-- CREATE SECURITY POLICY rls_customers ADD FILTER PREDICATE dbo.fn_rls_allow_user(USER_NAME())
-- ON erp_reporting.customers_curated;
-- GO
