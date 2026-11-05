					-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Search Data in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMSearchData]
	-- Add the parameters for the stored procedure here
	@CompanyNo tinyint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

		Declare @Procedure varchar(1000) =  (Select FSDD.ProcedureName 
													From GlobalData.FormSearchDataDetail FSDD
													Where FSDD.FormNo = 28
															And FSDD.InActive = 0
												) 
												+' '+ Convert(varchar(3),@CompanyNo)											
							
		      
		Exec (@Procedure)

end try
begin catch
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
				   ,'MSGM')
end catch

END















