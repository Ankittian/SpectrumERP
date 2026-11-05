

-- =============================================
-- Author:		Kirti
-- Create date: 15-Jun-23
-- Description:	Save Bin detail in Sub Group Master
-- =============================================
Create PROCEDURE [masterdata].[MSGMSaveBinDetail]
	-- Add the parameters for the stored procedure here
	@SubGroupNo smallint
   ,@BinNo smallint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here

	INSERT INTO [masterdata].[mBinCardSubgroupDetail] 
           ([SubGroupNo]
           ,[BinNo])
     VALUES
           (@SubGroupNo
           ,@BinNo)

	select 1
end try
begin catch
	select 0,Error_Message()
end catch

END













