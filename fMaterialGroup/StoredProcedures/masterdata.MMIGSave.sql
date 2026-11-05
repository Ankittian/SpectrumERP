
-- =============================================
-- Author:		Namrata
-- Create date: 17-Dec-11
-- Description:	Save Material Group Master
-- =============================================
CREATE Procedure [masterdata].[MMIGSave] 
			@GroupNo smallint
           ,@CategoryNo smallint
           ,@GroupCode varchar(2)
           ,@GroupName varchar(100)
           ,@LoginNo int
           ,@DocumentStatusNo tinyint = 30
           
AS
BEGIN
	
SET NOCOUNT ON;
BEGIN TRY

	If isnull(@GroupNo,0)=0
	BEGIN
		
		
		--- Inserting Details Of HeadOffice No's 
		INSERT INTO 
			[masterdata].[mGroupMaster]
			( [CategoryNo]
			,[Code]
			,[GroupName]
			,[CreatedBy]
			,[CreatedDate]
			,AuthorizedBy 
			,AuthorizedDate 
			,DocumentStatusNo)
			
			values(
				@CategoryNo 
				,@GroupCode 
				,@GroupName 
				,@LoginNo
				,GetDate() 
				,case when @DocumentStatusNo=30 then @LoginNo else null end
			,case when @DocumentStatusNo=30 then GETDATE ()else null end
			,@DocumentStatusNo)
		SELECT @GroupNo	= IDENT_CURRENT('[masterdata].[mGroupMaster]')				
		
		insert into [masterdata].mGroupMasterCompanyDetail (GroupNo ,CompanyNo , Inactive )
				select @GroupNo,companyno ,0
					from masterdata.mCompanyMaster 
									
	END
	ELSE
	BEGIN
	
	--New Code
	
		Delete From [masterdata].[mGroupQCParameterDetail] Where GroupNo = @GroupNo 
	
		-- Update Group Details For CHILD COMPANIES
		UPDATE [masterdata].[mGroupMaster]
		   SET  
			   [CategoryNo]= @CategoryNo 
			  ,[Code]= @GroupCode
			  ,[GroupName]= @GroupName
			  ,[ModifiedBy] = @LoginNo
			  ,[ModifiedDate] = getdate()
			  ,AuthorizedBy = case when @DocumentStatusNo=30 then @LoginNo else null end
			  ,AuthorizedDate = case when @DocumentStatusNo=30 then GETDATE ()else null end
			  ,DocumentStatusNo= @DocumentStatusNo
		Where GroupNo =@GroupNo 
 
		
		update IM set FullCode = CM.Code + gm.Code + sg.Code + IM.Code
		from masterdata.mItemMaster IM 
		inner join Masterdata.mSubGroupMaster sg on sg.SubgroupNo = im.SubGroupNo
		inner join Masterdata.mGroupMaster GM on gm.groupno = sg.GroupNo
		inner join Masterdata.mCategoryMaster CM on CM.CategoryNo = GM.CategoryNo
		where
		gm.GroupNo =@GroupNo 
		
		
	END

	SELECT 1,@GroupNo

END TRY 
BEGIN CATCH	
	SELECT 0,Error_message()
END CATCH
END


















