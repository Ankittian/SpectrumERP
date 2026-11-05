					


-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Load Data in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMLoadData]
	-- Add the parameters for the stored procedure here
	 @SubGroupNo smallint
	,@CompanyNo tinyint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here

 
--0
	select sgmd.MakeNo [Make Name],mm.Code [Code]
	from masterdata.mSubGroupMakeDetail sgmd
		inner join masterdata.mmakemaster mm on mm.makeno=sgmd.makeno
	where SubGroupNo=@SubGroupNo

--1
	SELECT     pcd.QCParameterNo [QC Parameter Name], qc.UnitNo [Unit], pcd.StandardValue [Standard Value]
			   ,CONVERT(Decimal(9,3),Null) as	[Standard Value2]
			   ,CONVERT(Decimal(9,3),Null) as	[Actual Value1]
			   ,CONVERT(Decimal(9,3),Null) as	[Actual Value2]	
	, pcd.ToleranceValue [Tolerance Value],qc.ToleranceTypeNo as [Tolerance Type]
			, qc.ToleranceUnit [Tolerance Unit], qc.DeductionOn [Deduction On], qc.FormulaType [Formula Type]
			, pcd.DeductionRate [Deduction Rate], pcd.DeductionType [Deduction Type], pcd.DoubleDeductionFrom [Double Deduction From]
	FROM         masterdata.mSubGroupQCParameterDetail pcd
		inner join masterdata.mQCParameters qc on qc.QCPArameterNo=pcd.QCPArameterNo
	where SubGroupNo=@SubGroupNo

--2
	select ut.UnitTypeNo [Unit Type],sgud.UnitNo [Unit Name]
	from GlobalData.unittype ut 
		left join masterdata.mSubGroupUnitDetail sgud on sgud.UnitTypeNo=ut.UnitTypeNo
													and SubGroupNo=@SubGroupNo

--3
	select sgvd.VendorNo [Vendor Name], sgvd.VendorLocationNo [Location]
	from masterdata.mSubGroupVendorDetail sgvd
	where SubGroupNo=@SubGroupNo

--4
	select sgm.*,sgmcd.Inactive,gm.categoryNo ,sgm.GSTCategoryNo,sgm.HSNSACCodeno from 
	masterdata.mSubGroupMaster sgm
	inner join masterdata.mSubGroupMasterCompanyDetail  sgmcd on sgmcd.SubGroupNo = sgm.SubGroupNo 
		inner join masterdata.mgroupmaster gm on gm.groupno=sgm.groupno
	where sgm.SubGroupNo=@SubGroupNo

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















