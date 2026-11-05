
-- =============================================
-- Author:		Namrata
-- Create date: 20 Dec 2011
-- Description:	Delete UNIT MASTER
-- =============================================
CREATE PROCEDURE [masterdata].[MMUMDelete]
@UnitNo SmallInt
AS
BEGIN
	SET NOCOUNT ON;
	BEGIN TRY
			Begin Transaction
			--Transaction Begins from here
			
	  -- Delete Details Table
				 Delete From masterdata.mUnitConversionDetail Where UnitNo  =@UnitNo 
				 Delete From masterdata.mUnitConversionDetail Where ConversionUnitNo=@UnitNo
				 Delete From masterdata.mSubGroupUnitDetail Where UnitNo =@UnitNo
					Delete From masterdata.mUnitMasterCompanyDetail  WHERE UnitNo =@UnitNo									
		-- Delete Main Table
				  Delete From masterdata.mUnitMaster WHERE UnitNo =@UnitNo
				Select 1,'Success'
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











