
-- =============================================
-- Author:		Namrata
-- Create date: 17 Dec 2011
-- Description:	Fill Values For Material Group
-- =============================================
CREATE PROCEDURE [masterdata].[MMIGFillValues]
	@CompanyNo int
	,@GroupNo SmallInt
AS
BEGIN
BEGIN TRY
	-- 0 Category Name
	SELECT 
			 cm.CategoryNo
			,CategoryName As [Category Name]
			,Code As [Code]
			,CategoryName Id  -- for fast entry grid
	FROM masterdata.mCategoryMaster cm
	inner join masterdata.mCategoryMasterCompanyDetail cmcd on cmcd.CategoryNo = cm.CategoryNo
	Where cmcd.CompanyNo=@CompanyNo And IsNull(cmcd.Inactive,0)=0
	UNION 
	SELECT 
			 GM.CategoryNo
			,CATM.CategoryName As [Category Name]
			,CATM.Code As [Code]
			,CategoryName Id
	FROM masterdata.mGroupMaster GM
	INNER JOIN masterdata.mCategoryMaster CATM ON CATM.CategoryNo=GM.CategoryNo
	Where  GM.GroupNo=@GroupNo
	
	-- 1 Fill Fast Entry Grid
	
	Select '' as [Category Name],'' as Code,'' as [Group Name],'' as Remarks
	Where 1 = 2	
	 
	
END TRY
BEGIN CATCH
	INSERT INTO [masterdata].[mErrorLog]
				   ([ErrorDate]
				   ,[ErrorNo]
				   ,[ErrorSeverity]
				   ,[ErrorState]
				   ,[ErrorProcedure]
				   ,[ErrorLine]
				   ,[ErrorDescription]
				   ,[UserName]
				   ,[FormCode])
			 VALUES
				   (getdate()
				   ,ERROR_NUMBER()
				   ,ERROR_SEVERITY()
				   ,ERROR_STATE()
				   ,ERROR_PROCEDURE()
				   ,ERROR_LINE()
				   ,ERROR_MESSAGE()
				   ,SUSER_SNAME()
				   ,'MMIG')
END CATCH
END











