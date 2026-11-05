
-- =============================================
-- Author:		<Alok>
-- Create date: <15 Dec 2011>
-- Description:	<Fill Values for QC Group Contol>
-- =============================================
CREATE PROCEDURE [masterdata].[QCFillValues]	
	@CompanyNo tinyint
AS
BEGIN
	
	SET NOCOUNT ON;

	BEGIN TRY

		--0 QC Group Name

			Select QC.QCGroupNo,QCGroupName as [QC Group Name]
			,Code as Code 
			From Masterdata.mQCGroup QC
			inner join Masterdata.mQCGroupCompanyDetail QCCD on QCCD.QCGroupNo = QC.QCGroupNo 
			Where CompanyNo=@CompanyNo And Inactive=0 and QC.AuthorizedBy is not null

	   	-- 1 Grid Fill Values
			Select Convert(int,Null) as [QC Parameter Name]
				   ,Convert(int,Null) as Unit
				   ,Convert(Decimal(9,3),Null) as [Standard Value]
				   ,Convert(Decimal(9,3),Null) as [Standard Value2]
				   ,Convert(Decimal(9,3),Null) as [Actual Value1]
				   ,Convert(Decimal(9,3),Null) as [Actual Value2]
				   ,Convert(Decimal(9,3),Null) as [Tolerance Value]
				   ,Convert(tinyint,Null) as [Tolerance Type]
				   ,Convert(tinyint,Null) as [Tolerance Unit]
				   ,Convert(tinyint,Null) as [Deduction On]
				   ,Convert(tinyint,Null) as [Formula Type]
				   ,Convert(tinyint,Null) as [Deduction Rate]	 
				   ,Convert(tinyint,Null) as [Deduction Type]	 
				   ,Convert(Decimal(9,3),Null) as [Double Deduction From]	
		    Where 1=2

		-- 2 QC Parameters
			SELECT qc.[QCParameterNo]            
			  ,[QCParameterName] as [QC Parameter Name]
			  ,[Code] as [Code]	
			  ,[UnitNo]
			  ,[StandardValue]
			  ,QC.StandardValue2 as [StandardValue2]
			  ,CONVERT(Decimal(9,3),Null ) as [ActualValue1]
			  ,CONVERT(Decimal(9,3),Null ) as [ActualValue2]
			  ,[ToleranceValue]
			  ,QC.ToleranceTypeNo as [ToleranceType]
			  ,[ToleranceUnit]
			  ,[DeductionOn]
			  ,[FormulaType]
			  ,[DeductionRate]
			  ,[DeductionType]
			  ,[DoubleDeductionFrom]
			  ,Inactive      
		  FROM [masterdata].[mQCParameters] QC
		  inner join [masterdata].[mQCParametersCompanyDetail] QCCD on QCCD.QCParameterNo = QC.QCParameterNo 
		  Where qccd.CompanyNo=@CompanyNo

		-- 3  Unit Names
			Select UM.UnitNo,Alias as [Unit],Code as Code
			From Masterdata.mUnitMaster UM
			inner join Masterdata.mUnitMasterCompanyDetail  UMCD on UMCD.UnitNo = UM.UnitNo 
			Where UMCD.CompanyNo=@CompanyNo and UMCD.Inactive =0 and  UM.AuthorizedBy is not null

		-- 4 Tolerance Type
			Select ToleranceTypeNo,ToleranceType as [Tolerance Type] 
			From GlobalData.QCToleranceType			
			Where Inactive=0			

		-- 5 
		   Select 1 as ID,'Lower value before Tolerance Limit' as [Deduction On]
		   Union
		   Select 2 as ID,'Higher value after Tolerance Limit'	
		   Order by Id	

		-- 6 Formula Type 
		   Select 1 as ID,'Rate' as [Formula Type]
		   Union
		   Select 2 as ID,'Quantity'	
		   Order by Id

		-- 7 Deduction Rate
			Select 1 as ID, 'Basic' as [Deduction Rate]
			Union
			Select 2 , 'Prorata' 
			Union
			Select 3 , 'Landed' 
			Order by Id

		-- 8  Deduction Type
			Select 1 as ID, 'Single' as [Deduction Type]
			Union
			Select 2 , 'Double' 			
			Order by Id
		
		-- 9 Fill Datatable 
			Select Convert(int,Null) as [QC Parameter Name]
				   ,Convert(int,Null) as Unit
				   ,Convert(Decimal(9,3),Null) as [Standard Value]
				   ,Convert(Decimal(9,3),Null) as [Standard Value2]
				   ,Convert(Decimal(9,3),Null) as [Actual Value1]
				   ,Convert(Decimal(9,3),Null) as [Actual Value2]
				   ,Convert(Decimal(9,3),Null) as [Tolerance Value]
				   ,Convert(tinyint,Null) as [Tolerance Type]
				   ,Convert(tinyint,Null) as [Tolerance Unit]
				   ,Convert(tinyint,Null) as [Deduction On]
				   ,Convert(tinyint,Null) as [Formula Type]
				   ,Convert(tinyint,Null) as [Deduction Rate]	 
				   ,Convert(tinyint,Null) as [Deduction Type]	 
				   ,Convert(Decimal(9,3),Null) as [Double Deduction From]				   

		-- 10  Tolerance Unit
			Select UM.UnitNo,Alias as [Tolerance Unit],Code as Code
			From Masterdata.mUnitMaster UM
			inner join Masterdata.mUnitMasterCompanyDetail  UMCD on UMCD.UnitNo = UM.UnitNo 
			Where UMCD.CompanyNo=@CompanyNo and UMCD.Inactive =0 and  UM.AuthorizedBy is not null		
			
		--11 QC ParameterDetail
		Select Convert(int,Null) as [QC Parameter Name]
				   ,Convert(int,Null) as Unit
				   ,Convert(varchar(100),Null) as [Expected Value]
				   ,Convert(varchar(300),Null) as [Remark]
		Where 1=2
		    
		--12 QC Hide QC Deduction
		Select IsHideQCDeduction from Config.DBCommonSetting

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
				   ,'ODDC')
	END CATCH   
	
END


















