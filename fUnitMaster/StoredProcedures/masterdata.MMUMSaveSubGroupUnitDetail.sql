

-- =============================================
-- Author:		 Namrata  
-- Create date:  20 Dec 2011
-- Description:	 Insert into SubGroupUnitDetail
-- =============================================
CREATE PROCEDURE [masterdata].[MMUMSaveSubGroupUnitDetail]
			@UnitNo smallint
           ,@SubGroupNo smallint
           ,@UnitTypeNo tinyint
         
AS    
BEGIN
	SET NOCOUNT ON;
	BEGIN TRY
	
	 
 
	--For Head Office
			INSERT INTO [masterdata].[mSubGroupUnitDetail]
									   (
									    [UnitNo]
									   ,[SubGroupNo]
									   ,[UnitTypeNo]
									   )
			values 
									  (
									    @UnitNo
									  , @SubGroupNo
									  , @UnitTypeNo 
									   )						   
						
															
												
	
			 SELECT 1
	END TRY
	BEGIN CATCH
	SELECT 0,ERROR_MESSAGE ()
	END CATCH
 
END












