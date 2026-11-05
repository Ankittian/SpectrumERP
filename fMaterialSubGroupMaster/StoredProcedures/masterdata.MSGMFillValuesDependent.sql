

-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Fill values dependent in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMFillValuesDependent]
	-- Add the parameters for the stored procedure here
	@CategoryNo smallint,
	@GroupNo smallint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here
--0
	select GroupNo,GroupName [Group Name],[Code]
	from masterdata.mGroupMaster
	where CategoryNo=@CategoryNo

-- table 1	
	select isnull(max(convert(smallint,Code)),0) + 1 [SubGroupCode] from Masterdata.mSubGroupMaster
	where GroupNo = @GroupNo and isnumeric(Code)=1
	
-- table 2
SELECT     pcd.QCParameterNo [QC Parameter Name], qc.UnitNo [Unit], pcd.StandardValue [Standard Value]
			   ,CONVERT(Decimal(9,3),Null) as	[Standard Value2]
			   ,CONVERT(Decimal(9,3),Null) as	[Actual Value1]
			   ,CONVERT(Decimal(9,3),Null) as	[Actual Value2]
			   , pcd.ToleranceValue [Tolerance Value]
			   ,qc.ToleranceTypeNo as [Tolerance Type]
			, qc.ToleranceUnit [Tolerance Unit], qc.DeductionOn [Deduction On], qc.FormulaType [Formula Type]
			, pcd.DeductionRate [Deduction Rate], pcd.DeductionType [Deduction Type], pcd.DoubleDeductionFrom [Double Deduction From]
	FROM         masterdata.mGroupQCParameterDetail pcd
		inner join masterdata.mQCParameters qc on qc.QCPArameterNo=pcd.QCPArameterNo
	where GroupNo = @GroupNo 

	

end try
begin catch
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
				   ,'MSGM')
end catch

END












