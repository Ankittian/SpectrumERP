


-- =============================================
-- Author:		<Alok>
-- Create date: <15 Dec 2011>
-- Description:	<Fill Parameters for QC Group>
-- =============================================
CREATE PROCEDURE [masterdata].[QCFillValuesDependent]	
	@QCGroupNo Smallint,
	@CompanyNo tinyint
AS
BEGIN
	
	SET NOCOUNT ON;

	BEGIN TRY

	-- 0 
		
		Select QCG.QCParameterNo as [QC Parameter Name]
			   ,QCP.UnitNo as [Unit]
			   ,QCG.StandardValue as	[Standard Value]
			   ,QCG.StandardValue2 as	[Standard Value2]
			   ,QCG.StandardValue as	[Actual Value1]
			   ,QCG.StandardValue2 as	[Actual Value2]			   
			   ,QCG.ToleranceValue as [Tolerance Value]
			   ,QCP.ToleranceTypeNo as [Tolerance Type]
			   ,QCP.ToleranceUnit as [Tolerance Unit]	
			   ,QCP.DeductionOn as [Deduction On]
			   ,QCP.FormulaType as [Formula Type]
			   ,QCG.DeductionRate as [Deduction Rate]	 
			   ,QCG.DeductionType as [Deduction Type]	 
			   ,QCG.DoubleDeductionFrom as [Double Deduction From]					   
		From masterdata.mQCGroupDetail QCG
		Inner Join  Masterdata.mQCParameters QCP on QCP.QCParameterNo=QCG.QCParameterNo  
		Inner Join  Masterdata.mQCParametersCompanyDetail QCPCD on QCP.QCParameterNo=QCPCD.QCParameterNo 
		Where QCG.QCGroupNo=@QCGroupNo and QCPCD.Inactive=0 and QCP.AuthorizedBy is not Null
			and QCPCD.CompanyNo =@CompanyNo 
			

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













