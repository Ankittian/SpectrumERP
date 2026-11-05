

-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Save Vendor detail in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMSaveVendor]
	-- Add the parameters for the stored procedure here
	@SubGroupNo smallint
   ,@VendorNo int
   ,@VendorLocationNo int
	,@CompanyNo tinyint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try
 

	INSERT INTO [masterdata].[mSubGroupVendorDetail]
           ([SubGroupNo]
           ,[VendorNo]
           ,[VendorLocationNo])
     VALUES
           (@SubGroupNo
           ,@VendorNo
           ,@VendorLocationNo)

	select 1
end try
begin catch
	select 0,Error_Message()
end catch

END













