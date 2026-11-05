-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Save Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMSaveMain] 
	-- Add the parameters for the stored procedure here
	@SubGroupNo smallint
   ,@GroupNo smallint
   ,@Code varchar(2)
   ,@SubGroupName varchar(100)
   ,@ReceiptTolerance decimal(5,2)
   ,@ShipmentTolerance decimal(5,2)
   ,@LoginNo smallint
   ,@DocumentStatusNo tinyint = 30
   ,@HSNSACCodeno smallint=Null
   ,@GSTCategoryNo tinyint=Null
   ,@IsBinApplicable bit = 0
   ,@DispatchNegTolerance decimal(5,2) = null
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try
    -- Insert statements for procedure here
	if isnull(@SubGroupNo,0)=0
	begin


		INSERT INTO [masterdata].[mSubGroupMaster]
			   ([GroupNo]
			   ,[Code]
			   ,[SubGroupName]
			   ,[ReceiptTolerance]
			   ,[ShipmentTolerance]
			   ,[CreatedBy]
			   ,[CreatedDate]
			   ,AuthorizedBy 
			   ,AuthorizedDate 
			   ,DocumentStatusNo
			   ,HSNSACCodeno
			   ,GSTCategoryNo
			   ,IsBinApplicable
			   ,DispatchNegTolerance)
		 values(
			    @GroupNo
			   ,@Code
			   ,@SubGroupName
			   ,@ReceiptTolerance
			   ,@ShipmentTolerance
			   ,@LoginNo
			   ,getdate()
			,case when @DocumentStatusNo=30 then @LoginNo else null end
			,case when @DocumentStatusNo=30 then GETDATE ()else null end
			,@DocumentStatusNo
			,@HSNSACCodeno 
			,@GSTCategoryNo
			,@IsBinApplicable
			,@DispatchNegTolerance)

		select @SubGroupNo=ident_current('[masterdata].[mSubGroupMaster]')
		
		insert into [masterdata].mSubGroupMasterCompanyDetail (SubGroupNo  ,CompanyNo , Inactive )
				select @SubGroupNo,companyno ,0
					from masterdata.mCompanyMaster 
	end
	else
	begin
		 

		delete from masterdata.mBinCardSubgroupDetail where SubGroupNo = @SubGroupNo 

		delete sd 
		from masterdata.mSubGroupDivisionDetail sd where SubGroupNo =@SubGroupNo 
			 
		delete from masterdata.mSubGroupMakeDetail where SubGroupNo =@SubGroupNo 

		delete from masterdata.mSubGroupQCParameterDetail where SubGroupNo =@SubGroupNo 
		delete from masterdata.mSubGroupUnitDetail where SubGroupNo =@SubGroupNo 

		delete from masterdata.mSubGroupVendorDetail where SubGroupNo =@SubGroupNo 

		UPDATE [masterdata].[mSubGroupMaster]
		   SET [GroupNo] = @GroupNo
			  ,[Code] = @Code
			  ,[SubGroupName] = @SubGroupName
			  ,[ReceiptTolerance] = @ReceiptTolerance
			  ,[ShipmentTolerance] = @ShipmentTolerance
			  ,[ModifiedBy] = @LoginNo
			  ,[ModifiedDate] = getdate()
			   ,AuthorizedBy = case when @DocumentStatusNo=30 then @LoginNo else null end
			  ,AuthorizedDate = case when @DocumentStatusNo=30 then GETDATE ()else null end
			  ,DocumentStatusNo= @DocumentStatusNo
			  ,HSNSACCodeno = @HSNSACCodeno
			  ,GSTCategoryNo = @GSTCategoryNo
			  ,IsBinApplicable = @IsBinApplicable
			  ,DispatchNegTolerance = @DispatchNegTolerance
		Where SubGroupNo =@SubGroupNo
			
	update IM set FullCode = CM.Code + gm.Code + sg.Code + IM.Code
		from masterdata.mItemMaster IM 
		inner join Masterdata.mSubGroupMaster sg on sg.SubgroupNo = im.SubGroupNo
		inner join Masterdata.mGroupMaster GM on gm.groupno = sg.GroupNo
		inner join Masterdata.mCategoryMaster CM on CM.CategoryNo = GM.CategoryNo
		where
		sg.SubGroupNo = @SubGroupNo 
			
		
	end
	
	select 1,@SubGroupNo

end try
begin catch
	select 0,Error_Message()
end catch

END



















