
-- =============================================
-- Author:		NAMRATA
-- Create date: 20-Dec-11
-- Description:	Validate Unit master
-- =============================================
CREATE PROCEDURE [masterdata].[MMUMValidate] 
	
	 @UnitName varchar(25)
	,@UnitNo smallint
	,@CompanyNo smallint
	,@Alias varchar(6)
AS
BEGIN
	SET NOCOUNT ON;
Begin Try
    
	If Exists 
			(
				Select 1
				from masterdata.mUnitMaster um
				inner join masterdata.mUnitMasterCompanyDetail umcd on umcd.UnitNo = um.UnitNo 
				where UnitName = @UnitName
				And CompanyNo=@CompanyNo
				And um.UnitNo <> isnull(@UnitNo,0))
				
				BEGIN 
				select 0,'Duplicate Unit Name is not allowed.',1		
				RETURN
				END
		
	   
	   If Exists 
			(
				Select 1
				from masterdata.mUnitMaster um
				inner join masterdata.mUnitMasterCompanyDetail umcd on umcd.UnitNo = um.UnitNo 
				where Alias=@Alias
				And umcd.CompanyNo=@CompanyNo
				And um.UnitNo <> isnull(@UnitNo,0))
				BEGIN 
				select 0,'Duplicate Alias is not allowed.',2		
				RETURN
				END
		
	   
		select 1
End Try 
Begin Catch
		Select 0,Error_message() 
End Catch 
END













