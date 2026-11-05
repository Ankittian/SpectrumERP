
-- =============================================
-- Author:		 Namrata  
-- Create date:  17 Dec 2011
-- Description:	 insert into GroupQCParameter Details
-- =============================================
CREATE PROCEDURE [masterdata].[MMIGSaveQCParameter]
			@GroupNo smallint
           ,@QCParameterNo smallint
           ,@StandardValue decimal(9,3)
           ,@ToleranceValue decimal(9,3)
           ,@DeductionRate tinyint
           ,@DeductionType tinyint
           ,@DoubleDeductionFrom decimal(9,3)
AS    
BEGIN
	SET NOCOUNT ON;
	BEGIN TRY
			
			 INSERT INTO [masterdata].[mGroupQCParameterDetail]
											   ([GroupNo]
											   ,[QCParameterNo]
											   ,[StandardValue]
											   ,[ToleranceValue]
											   ,[DeductionRate]
											   ,[DeductionType]
											   ,[DoubleDeductionFrom]
											   )
				Values
											   (@GroupNo
											   ,@QCParameterNo
											   ,@StandardValue 
											   ,@ToleranceValue
											   ,@DeductionRate 
											   ,@DeductionType 
											   ,@DoubleDeductionFrom	
											   )				   							
	
			 SELECT 1
	END TRY
	BEGIN CATCH
	SELECT 0,ERROR_MESSAGE ()
	END CATCH
 
END












