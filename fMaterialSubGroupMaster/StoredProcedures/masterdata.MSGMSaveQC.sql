

-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Save QC Parameter detail in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMSaveQC]
	-- Add the parameters for the stored procedure here
	@SubGroupNo smallint
   ,@QCParameterNo smallint
   ,@StandardValue decimal(9,3)
   ,@ToleranceValue decimal(9,3)
   ,@DeductionRate tinyint
   ,@DeductionType tinyint
   ,@DoubleDeductionFrom decimal(9,3)
	,@CompanyNo tinyint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here

	INSERT INTO [masterdata].[mSubGroupQCParameterDetail]
           ([SubGroupNo]
           ,[QCParameterNo]
           ,[StandardValue]
           ,[ToleranceValue]
           ,[DeductionRate]
           ,[DeductionType]
           ,[DoubleDeductionFrom])
     VALUES
           (@SubGroupNo
           ,@QCParameterNo
           ,@StandardValue
           ,@ToleranceValue
           ,@DeductionRate
           ,@DeductionType
           ,@DoubleDeductionFrom)

	select 1
end try
begin catch
	select 0,Error_Message()
end catch

END













