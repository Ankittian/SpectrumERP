



-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	delete from Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMDelete]
	-- Add the parameters for the stored procedure here
	@SubGroupNo smallint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here
	
begin transaction

	Delete from masterdata.mBinCardSubgroupDetail where SubGroupNo = @SubGroupNo  
	delete from masterdata.mSubGroupTechnicalGrade  where SubGroupNo =@SubGroupNo 

	delete from masterdata.mSubGroupDivisionDetail where SubGroupNo =@SubGroupNo 
	delete from masterdata.mSubGroupMakeDetail where SubGroupNo =@SubGroupNo 

	delete from masterdata.mSubGroupQCParameterDetail where SubGroupNo =@SubGroupNo 
	delete from masterdata.mSubGroupUnitDetail where SubGroupNo =@SubGroupNo 

	delete from masterdata.mSubGroupVendorDetail where SubGroupNo =@SubGroupNo 
	delete from masterdata.mSubGroupMasterCompanyDetail where SubGroupNo =@SubGroupNo 
	delete from masterdata.mSubGroupMaster  where  SubGroupNo =@SubGroupNo  
commit transaction
	select 1

end try
begin catch
	rollback transaction
	select 0,Error_Message()
end catch

END















