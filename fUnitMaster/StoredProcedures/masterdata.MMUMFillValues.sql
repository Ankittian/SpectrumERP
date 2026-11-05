
-- =============================================
-- Author:		NAMRATA
-- Create date: 19 Dec 2011
-- Description:	Unit MASTER Fill Values
-- =============================================
CREATE PROCEDURE [masterdata].[MMUMFillValues]
	 @CompanyNo tinyint
	,@UnitNo smallint
AS
BEGIN	
	SET NOCOUNT ON;
	BEGIN TRY

	-- 0 CategoryName Combo
		Select 
			  UnitCategoryno
			 ,CategoryName Id
			 ,CategoryName As [Category Name]	
		From GlobalData.UnitCategory
		
		
		
	-- 1 Standard Conversion Factor
		Select
				 Convert(Int,Null) AS [Conversion Type]
				, Convert(Decimal(7,3),Null) AS [Unit Value]
				,'' AS [Base Unit]
				, Convert(Decimal(7,3),Null) AS [Conversion Value]
				, Convert(Int,Null) AS [Unit]
		Where 1=2
		
	-- 2 [Conversion Type]
	    SELECT 1 AS [ID],'Fixed' AS [Conversion Type]
	    UNION ALL
		SELECT 2,'Variable'
		
	-- 3 Unit Combo
		Select 
			   um.UnitNo
			  ,Alias As [Unit Name]
			  ,Alias
			  ,Code
		from masterdata.mUnitMaster um
		inner join masterdata.mUnitMasterCompanyDetail umcd on umcd.UnitNo = um.UnitNo
		Where umcd.CompanyNo=@CompanyNo And IsNull(umcd.Inactive,0)=0
		And um.unitNo <>@unitNo
		Union
		Select 
			   ConversionUnitNo As [UnitNo]
			  ,UM.Alias As [Unit Name]
			  ,UM.Alias
			  ,UM.Code
		from masterdata.mUnitConversionDetail UCD
		INNER JOIN masterdata.mUnitMaster UM ON UM.UnitNo=UCD.ConversionUnitNo
		inner join masterdata.mUnitMasterCompanyDetail umcd on umcd.UnitNo = um.UnitNo
		Where umcd.CompanyNo=@CompanyNo
		And UCD.UnitNo=@UnitNo
		
		
	-- 4 Material Subgroup GRID
		Select
				 Convert(Int,Null) AS[Subgroup Name]
				,'' AS [Subgroup Code]
				,Convert(Int,Null) As [Unit Type]
		Where 1=2
	
	-- 5 [Subgroup Name]
	Select 
		   SGM.SubGroupNo
		  ,SGM.SubGroupName As [SubGroup Name]
		  ,GM.GroupName As [Group Name]
		  ,SGM.Code As [Code]
	From masterdata.mSubgroupmaster SGM
	inner join masterdata.mSubGroupMasterCompanyDetail  SGMcd on SGMcd .SubGroupNo = SGM.SubGroupNo 
	INNER JOIN masterdata.mGroupMaster GM ON GM.GroupNo=SGM.GroupNo 
	Where SGMcd.CompanyNo=@CompanyNo
	And IsNull(SGMcd.Inactive,0)=0
    Union
	Select 
			 SGUD.SubGroupNo
			,SGM.SubGroupName As [SubGroup Name]
			,GM.GroupName As [Group Name]
			,SGM.Code As [Code]
	From masterdata.mSubGroupUnitDetail SGUD 
	INNER JOIN masterdata.mSubgroupmaster SGM ON SGM.SubGroupNo= SGUD.SubGroupNo 
	INNER JOIN masterdata.mGroupMaster GM ON GM.GroupNo=SGM.GroupNo 
	And SGUD.UnitNo=@UnitNo

 -- 6  [Unit Type]
	 Select 
			UnitTypeNo
		   ,UnitTypeName As [Unit Type]
	 From GlobalData.UnitType
	 
--  7 Fill Fast ENtry Grid

   Select '' as [Unit Name]
		 ,'' as [Alias]
		 ,'' as [Category]
		 , '' as [Remarks] 
   Where 1=2

--  8 Fill GST UQC combo
   Select GstUnitNo,Code,UnitName [Unit Name] from GlobalData.GSTUnitMaster
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
				   ,'MMUM')
	END CATCH    
END











