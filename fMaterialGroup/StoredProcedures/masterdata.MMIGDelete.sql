
-- =============================================
-- Author:		Namrata
-- Create date: 19 Dec 2011
-- Description:	Delete Material Group
-- =============================================
CREATE PROCEDURE [masterdata].[MMIGDelete]
@GroupNo SmallInt
AS
BEGIN
	SET NOCOUNT ON;
	BEGIN TRY
			Begin Transaction
			--Transaction Begins from here
			
				-- Delete Detail Table
				 Delete From [masterdata].[mGroupQCParameterDetail] where GroupNo = @GroupNo 
				 Delete From [masterdata].[mGroupMasterCompanyDetail] where GroupNo = @GroupNo 
				 -- Delete Main Table
				  Delete From [masterdata].[mGroupMaster] FROM [masterdata].[mGroupMaster]WHERE GroupNo =@GroupNo
				  
				Select 1
			--Transaction Ends here
			Commit Transaction
		
	END TRY
	--Try Block ends here
	--Catch Block starts here
	BEGIN CATCH
		Rollback Transaction
		SELECT 0,ERROR_MESSAGE()
	END CATCH
	--Catch Block ends here
END











