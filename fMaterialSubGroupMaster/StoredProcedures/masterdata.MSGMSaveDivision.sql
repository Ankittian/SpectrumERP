


-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Save division detail in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMSaveDivision]
	-- Add the parameters for the stored procedure here
	@DivisionNo int
    ,@SubGroupNo smallint
	,@WHCompanyNo tinyint
	,@warehouseNo smallint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here
   
	INSERT INTO [masterdata].[mSubGroupDivisionDetail]
           ([SubGroupNo],
           [DivisionNo],
           [WarehouseNo],
           [CompanyNo])
	values (@SubGroupNo,
			@DivisionNo ,
			@warehouseNo ,
			@WHCompanyNo) 
	

	select 1
end try
begin catch
	select 0,Error_Message()
end catch

END














