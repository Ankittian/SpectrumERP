

-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Save Make detail in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMSaveMake]
	-- Add the parameters for the stored procedure here
	@SubGroupNo smallint
    ,@MakeNo smallint
	,@CompanyNo tinyint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here
	INSERT INTO [masterdata].[mSubGroupMakeDetail]
           ([SubGroupNo]
           ,[MakeNo])
     VALUES
           (@SubGroupNo
           ,@MakeNo)

	select 1

end try
begin catch
	select 0,Error_Message()
end catch

END













