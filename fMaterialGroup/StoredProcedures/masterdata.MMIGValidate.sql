
-- =============================================
-- Author:		NAMRATA
-- Create date: 19-Dec-11
-- Description:	Validate Material Group master
-- =============================================
CREATE PROCEDURE [masterdata].[MMIGValidate] 
	
	@GroupName varchar(100), 
	@GroupNo smallint
	,@CompanyNo smallint
	,@CategoryNo smallint
	,@GroupCode varchar(2)
AS
BEGIN
	SET NOCOUNT ON;
Begin Try
    
	If Exists 
			(
				Select 1
				from [MasterData].[mGroupMaster] gm
					inner join masterdata.mGroupMasterCompanyDetail gmcd on gmcd.GroupNo=gm.GroupNo 
				where GroupName = @GroupName and CategoryNo = @CategoryNo 
				And gmcd.CompanyNo=@CompanyNo And gm.GroupNo <> isnull(@GroupNo,0))
			BEGIN
			select 0,'Duplicate Group Name is not allowed.',1
			RETURN
			END
		
	   
	   If Exists 
			(
				Select 1
				from [MasterData].[mGroupMaster]
				where Code=@GroupCode
				And CategoryNo=@CategoryNo
				And GroupNo <> isnull(@GroupNo,0))
			BEGIN
			select 0,'Duplicate Group Code is not allowed.',2
			RETURN
			END
		
	   
		select 1
End Try 
Begin Catch
		Select 0,Error_message() 
End Catch 
END






