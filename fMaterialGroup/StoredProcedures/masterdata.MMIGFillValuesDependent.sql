
-- =============================================
-- Author:		<Namrata>
-- Create date: <19 Dec 2011>
-- Description:	<Fill Value Dependent From Material Group>
-- =============================================
CREATE PROCEDURE [masterdata].[MMIGFillValuesDependent]	
	@CategoryNo Smallint
AS
BEGIN
	
	SET NOCOUNT ON;

	BEGIN TRY

	-- 0  CODE
	Select 
		  Right(Replicate('0',2)+Convert(Varchar,IsNull(Max(Code),0)+1),2)
	From masterdata.mGroupMaster
	Where CategoryNo=@CategoryNo 
	And IsNumeric(Code)=1


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










