
-- =============================================
-- Author:		 Namrata  
-- Create date:  20 Dec 2011
-- Description:	 insert into Standard Conversion Factor
-- =============================================
CREATE PROCEDURE [masterdata].[MMUMSaveUnitConversionDetail]
			@UnitNo smallint
           ,@ConversionType tinyint
           ,@FirstCF decimal(8,3)
           ,@SecondCF decimal(8,3)
           ,@ConversionUnitNo smallint
AS    
BEGIN
	SET NOCOUNT ON;
	BEGIN TRY
	
  
			INSERT INTO [masterdata].[mUnitConversionDetail]
											   (
											    [UnitNo]
											   ,[ConversionType]
											   ,[FirstCF]
											   ,[SecondCF]
											   ,[ConversionUnitNo])
			Values
											   (
											     @UnitNo
											    ,@ConversionType 
											    ,@FirstCF 
											    ,@SecondCF 
											    ,@ConversionUnitNo 
											   )								   


	 
			INSERT INTO [masterdata].[mUnitConversionDetail]
											   (
											    [UnitNo]
											   ,[ConversionType]
											   ,[FirstCF]
											   ,[SecondCF]
											   ,[ConversionUnitNo])
			Values
											   (
											     @ConversionUnitNo
											    ,@ConversionType 
											    ,@SecondCF 
											    ,@FirstCF 
											    , @UnitNo
											   )		



			 SELECT 1
	END TRY
	BEGIN CATCH
	SELECT 0,ERROR_MESSAGE ()
	END CATCH
 
END












