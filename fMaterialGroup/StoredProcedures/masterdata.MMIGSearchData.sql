					
-- =============================================
-- Author:		Namrata
-- Create date: 17-Dec-11
-- Description:	Search data of Material Group Master niros
-- =============================================
CREATE PROCEDURE [masterdata].[MMIGSearchData]

	@CompanyNo tinyint
AS
BEGIN
	SET NOCOUNT ON;
Begin Try


		Declare @Procedure varchar(1000) =  (Select FSDD.ProcedureName 
													From GlobalData.FormSearchDataDetail FSDD
													Where FSDD.FormNo = 26
															And FSDD.InActive = 0
												) 
												+' '+ Convert(varchar(3),@CompanyNo)											
							
		      
		Exec (@Procedure)
		
		
		
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
				   ,'MMIG')
End Catch 
END














