
-- =============================================
--  Author:		Namrata
-- Create date: 20-Dec-2011
-- Description:	Load Unit Master
-- =============================================
CREATE PROCEDURE [masterdata].[MMUMLoadData] 
	@UnitNo Smallint,
	@CompanyNo tinyint
AS
BEGIN
	SET NOCOUNT ON;
Begin Try
   
    --- 0 Unit Master
	SELECT 
	   [Code]
	  ,[UnitName]
	  ,[Alias]
	  ,[UnitCategoryNo]
	  ,umcd.[Inactive]
	  ,[GSTUnitNo]
	FROM [masterdata].[mUnitMaster] um
	inner join [masterdata].[mUnitMasterCompanyDetail]  umcd on umcd.UnitNo = um.UnitNo and umcd.CompanyNo =@CompanyNo 
	Where um.UnitNo=@UnitNo
	
	--- 1 UnitConversionDetail
	
	SELECT 
	   [ConversionType] AS [Conversion Type]
      ,[FirstCF] AS [Unit Value]
      , '' AS [Base Unit]
      ,[SecondCF]  AS [Conversion Value]
      ,[ConversionUnitNo] AS [Unit]
  FROM [masterdata].[mUnitConversionDetail]
  Where UnitNo=@UnitNo
  
  -- 2 Material Subgroup
  SELECT 
       SGUD.SubGroupNo AS[Subgroup Name]
      ,SGM.Code AS [Subgroup Code]
      ,[UnitTypeNo] As [Unit Type]
  FROM [masterdata].[mSubGroupUnitDetail] SGUD
  INNER JOIN masterdata.mSubGroupMaster SGM ON SGM.SubGroupNo=SGUD.SubGroupNo
   Where UnitNo=@UnitNo
	
End Try 

Begin Catch
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
				   ,'MMUM')
End Catch 
END













