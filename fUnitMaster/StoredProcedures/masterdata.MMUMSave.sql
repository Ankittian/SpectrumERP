
-- =============================================
-- Author:		Namrata
-- Create date: 20-Dec-11
-- Description:	Save Material Unit Master
-- =============================================
CREATE Procedure [masterdata].[MMUMSave] 
			@UnitNo smallint
           ,@UnitName varchar(25)
           ,@Alias varchar(6)
           ,@UnitCategoryNo tinyint
           ,@LoginNo int
           ,@DocumentStatusNo tinyint = 30
           ,@GSTUQC tinyint
AS
BEGIN
	
SET NOCOUNT ON;
BEGIN TRY

	If isnull(@UnitNo,0)=0
	BEGIN
		
		
		Declare @Code char(6)
			SELECT @Code = 'UM'+ RIGHT(REPLICATE('0', 4) +cast(isnull(max(Convert(int,substring(Code,3,4))),0) + 1 as varchar(4)),4)  
			FROM  [masterdata].[mUnitMaster]
			
		
		--- Inserting Details Of HeadOffice No's 
		INSERT INTO [masterdata].[mUnitMaster]
				([Code]
				,[UnitName]
				,[Alias]
				,[UnitCategoryNo]
				,[CreatedBy]
				,[CreatedDate]
				,AuthorizedBy 
			   ,AuthorizedDate 
			   ,DocumentStatusNo
			   ,GSTUnitNo) 
			values (@Code
					,@UnitName 
					,@Alias
					,@UnitCategoryNo
					,@LoginNo
					,GetDate() 
					,case when @DocumentStatusNo=30 then @LoginNo else null end
			,case when @DocumentStatusNo=30 then GETDATE ()else null end
			,@DocumentStatusNo
			,@GSTUQC)		
				
		SELECT @UnitNo	= IDENT_CURRENT('[masterdata].[mUnitMaster]')				
		insert into [masterdata].mUnitMasterCompanyDetail (UnitNo ,CompanyNo , Inactive )
				select @UnitNo ,companyno ,0
					from masterdata.mCompanyMaster 
									
	END
	ELSE
	BEGIN
	
	  
	  -- Delete Details Table
				 Delete From masterdata.mUnitConversionDetail  Where ConversionUnitNo =@UnitNo 
				
				delete From masterdata.mUnitConversionDetail Where UnitNo =@UnitNo 
														
				 Delete From masterdata.mSubGroupUnitDetail Where UnitNo =@UnitNo 
														
												
		-- Update Unit Details For Every Company
		UPDATE [masterdata].[mUnitMaster]
		   SET 
			   [UnitName] = @UnitName
			  ,[Alias] = @Alias
			  ,[UnitCategoryNo] =@UnitCategoryNo
			  ,[ModifiedBy] = @LoginNo
			  ,[ModifiedDate] = getdate()
			  ,AuthorizedBy = case when @DocumentStatusNo=30 then @LoginNo else null end
			  ,AuthorizedDate = case when @DocumentStatusNo=30 then GETDATE ()else null end
			  ,DocumentStatusNo= @DocumentStatusNo
			  ,GSTUnitNo = @GSTUQC 
		WHERE UnitNo =@UnitNo 
	 
	END

	SELECT 1,@UnitNo

END TRY 
BEGIN CATCH	
	SELECT 0,Error_message()
END CATCH
END


















