

-- =============================================
--  Author:		Namrata
-- Create date: 19-Dec-2011
-- Description:	Load Material Group
-- =============================================
CREATE PROCEDURE [masterdata].[MMIGLoadData] 
	@GroupNo Smallint,
	@CompanyNo tinyint
AS
BEGIN
	SET NOCOUNT ON;
Begin Try
   
    --- 0 Group Details
	SELECT   
			   GM.Code GroupCode, 
			   GM.CategoryNo, 
			   GM.GroupName,
			   Gmcd.InActive
	FROM  [masterdata].[mGroupMaster] GM
	inner join [masterdata].[mGroupMasterCompanyDetail] GMcd on GMcd.GroupNo = GM.GroupNo 
	WHERE GM.GroupNo = @GroupNo
	
	--- 1 QC parameter
	
	SELECT 
			QCPD.QCParameterNo as [QC Parameter Name]
			,UnitNo As [Unit]
			,QCPD.StandardValue  as [Standard Value]
		    ,CONVERT(Decimal(9,3),Null) as	[Standard Value2]
		    ,CONVERT(Decimal(9,3),Null) as	[Actual Value1]
		    ,CONVERT(Decimal(9,3),Null) as	[Actual Value2]			
			,QCPD.ToleranceValue as [Tolerance Value]
			,QCP.ToleranceTypeNo as [Tolerance Type]
			,QCP.ToleranceUnit as [Tolerance Unit]
			,QCP.DeductionOn as [Deduction On]
			,QCP.FormulaType as [Formula Type]
			,QCPD.DeductionRate as [Deduction Rate]
			,QCPD.DeductionType as [Deduction Type]
			,QCPD.DoubleDeductionFrom as [Double Deduction From]	
	FROM [masterdata].[mGroupQCParameterDetail] QCPD
	INNER JOIN masterdata.mQCParameters QCP ON QCP.QCParameterNo=QCPD.QCParameterNo
	WHERE GroupNo = @GroupNo
	
End Try 

Begin Catch
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
End Catch 
END














