
-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Validate in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMValidate]
	-- Add the parameters for the stored procedure here
	@CompanyNo tinyint
	,@FullSubGroupCode varchar(6)
	,@SubGroupNo smallint
	,@SubGroupName varchar(100)
	,@GroupNo smallint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here
	if exists (select 1 from masterdata.msubgroupmaster sgm
				inner join masterdata.mSubGroupMasterCompanyDetail sgmcd on sgmcd.SubGroupNo = sgm.SubGroupNo 
					inner join masterdata.mgroupmaster gm on sgm.groupNo=gm.groupNo
					inner join masterdata.mCategorymaster cm on gm.CategoryNo=cm.CategoryNo
				where cm.code+gm.code+sgm.Code=@FullSubGroupCode and sgmcd.CompanyNo=@CompanyNo 
				and sgm.SubGroupNo<>isnull(@SubGroupNo,0))
	begin
		select 0,'Duplicate Sub Group Code is not allowed.'
		return
	end

	else if exists (select 1 from masterdata.mSubGroupMaster sgm
				where sgm.GroupNo = @GroupNo and sgm.SubGroupName = @SubGroupName 
				and sgm.SubGroupNo<>isnull(@SubGroupNo,0))
	begin
		select 0,'Duplicate Sub Group Name is not allowed.'
		return
	end
	
	select 1,'Success'
end try
begin catch
	select 0,Error_Message()
end catch

END











