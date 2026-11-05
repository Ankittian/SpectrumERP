
-- =============================================
-- Author:		Namrata
-- Create date: 20-Dec-11
-- Description:	Search data of UNIT MASTER
-- =============================================
CREATE PROCEDURE [masterdata].[MMUMSearchData]

	@CompanyNo tinyint
AS
BEGIN
	SET NOCOUNT ON;
Begin Try

	      SELECT 
					 um.UnitNo
					,UM.Code  As [Code]
					,UnitName As [Unit Name]
					,Alias
					,CatM.CategoryName As [Category Name]
					,UMcd.Inactive
					,SL.PrintingName as [Created By]
					,UM.CreatedDate AS [Created Date]
		  FROM masterdata.mUnitMaster UM
		  inner join masterdata.mUnitMasterCompanyDetail  UMcd on UMcd.UnitNo = UM.UnitNo 
		  INNER JOIN GlobalData.UnitCategory CatM ON CatM.UnitCategoryNo=uM.UnitCategoryNo 
		  left Join  Security.Login SL ON SL.LoginNo =UM.CreatedBy
		  Where uMcd.CompanyNo=@CompanyNo
		  ORDER BY [Unit Name]
		
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













