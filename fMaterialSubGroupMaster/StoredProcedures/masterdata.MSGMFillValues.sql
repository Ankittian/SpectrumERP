					


-- =============================================
-- Author:		Yusuf
-- Create date: 17-Dec-11
-- Description:	Fill values in Sub Group Master
-- =============================================
CREATE PROCEDURE [masterdata].[MSGMFillValues]
	-- Add the parameters for the stored procedure here
	@CompanyNo tinyint,
	@SubGroupNo smallint
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

begin try

    -- Insert statements for procedure here

--0

declare @IsDivisionApplicable bit,@whCompanyNo tinyint,@InterCode smallint
select @whCompanyNo= ISNULL(HeadOFficeNo,CompanyNo)
		from masterdata.mCompanyMaster where CompanyNo =@CompanyNo 
select @IsDivisionApplicable = IsDivisionApplicable  
		from masterdata.mCompanyMaster where CompanyNo =@whCompanyNo 


	select cast(case when sdd.CompanyNo is null then 0 else 1 end as bit) [Select],
			WareHouseName [Warehouse] ,dm.DivisionName [Division],cm.AliasName [Company], wdd.DivisionNo,
			wdd.CompanyNo,wdd.WarehouseNo 
	from 
	masterdata.mWarehouse  wm
	inner join masterdata .mWarehouseDivisionDetail wdd on wdd.WarehouseNo = wm.WareHouseNo 
	inner join masterdata .mCompanyMaster cm on cm.CompanyNo = wdd.CompanyNo 
	left join payroll.tblDivisionMaster dm on dm.DivisionNo= wdd.DivisionNo  
				and @IsDivisionApplicable =1 AND dm.IsActive =1
	left join masterdata .mSubGroupDivisionDetail sdd on sdd.companyNo= wdd.CompanyNo and 
			ISNULL(sdd.DivisionNo ,0) =ISNULL(wdd.DivisionNo,0) and wdd.WarehouseNo = sdd.warehouseNo
				and sdd.SubGroupNo =@SubGroupNo 
	where  wm.Inactive =0
	order by 1  desc
	
	
 --if exists(select 1 from masterdata .mCompanyMaster where HeadOfficeNo =@whCompanyNo)  		
--	select cast(case when sdd.CompanyNo is null then 0 else 1 end as bit) [Select],
--			WareHouseName [Warehouse] ,dm.DivisionName [Division],cm.AliasName [Company], wdd.DivisionNo,
--			wdd.CompanyNo,wdd.WarehouseNo 
--	from 
--	masterdata .mWarehouse wm
--	inner join masterdata .mWarehouseDivisionDetail wdd on wdd.WarehouseNo = wm.WareHouseNo 
--	inner join masterdata .mCompanyMaster cm on cm.CompanyNo = wdd.CompanyNo 
--	left join payroll.tblDivisionMaster dm on dm.DivisionNo= wdd.DivisionNo  and dm.InActive =0
--				and @IsDivisionApplicable =1
--	left join 
--	(select sdd.CompanyNo ,sdd.Divisionno,sdd.warehouseNo  from 
--			masterdata .mSubGroupDivisionDetail sdd ,masterdata.mSubGroupMaster sgm,masterdata.mSubGroupMaster
--				 sgm1
--			where sgm1.InternalCode = sgm.InternalCode  and sgm.CompanyNo= sdd.CompanyNo 
--				 and sdd.SubGroupNo = sgm.SubGroupNo and sgm1.subgroupno = @SubGroupNo 
--			) sdd on sdd.companyNo= cm.CompanyNo and 
--						ISNULL(sdd.DivisionNo ,0) = wdd.DivisionNo and wdd.WarehouseNo = sdd.warehouseNo
--	where  HeadOfficeNo is not null and wm.Inactive =0
--	order by 1  desc
--else
--	select cast(case when sdd.CompanyNo is null then 0 else 1 end as bit) [Select],
--			WareHouseName [Warehouse] ,dm.DivisionName [Division],cm.AliasName [Company], wdd.DivisionNo,
--			wdd.CompanyNo ,wdd.WarehouseNo
--	from 
--	masterdata .mWarehouse wm
--	inner join masterdata .mWarehouseDivisionDetail wdd on wdd.WarehouseNo = wm.WareHouseNo 
--	inner join masterdata .mCompanyMaster cm on cm.CompanyNo = wdd.CompanyNo 
--	left join payroll.tblDivisionMaster dm on dm.DivisionNo= wdd.DivisionNo  and dm.InActive =0
--					and @IsDivisionApplicable =1
--	left join(select sdd.CompanyNo ,sdd.Divisionno,sdd.warehouseNo  from 
--			masterdata .mSubGroupDivisionDetail sdd ,masterdata.mSubGroupMaster sgm,masterdata.mSubGroupMaster
--				 sgm1
--			where sgm1.InternalCode = sgm.InternalCode  and sgm.CompanyNo= sdd.CompanyNo 
--				 and sdd.SubGroupNo = sgm.SubGroupNo and sgm1.subgroupno = @SubGroupNo 
--			) sdd on sdd.companyNo= cm.CompanyNo and 
--						ISNULL(sdd.DivisionNo ,0) = wdd.DivisionNo and wdd.WarehouseNo = sdd.warehouseNo
--	where HeadOfficeNo is null and wm.Inactive =0
--	order by 1  desc


--1
	select null [Make Name],'' [Code] where 1=2

--2
	select mm.MakeNo, mm.MakeName [Make Name],mm.Code [Code]
	from masterdata.mMakeMaster mm 
	inner join masterdata.mMakeMasterCompanyDetail mmcd on mmcd.MakeNo = mm.MakeNo 
	left join masterdata.mSubGroupMakeDetail sd on sd.MakeNo = mm.MakeNo and sd.SubGroupNo =@SubGroupNo 
	where mmcd.CompanyNo=@CompanyNo and (mmcd.Inactive =0 or SubGroupNo is not null)
	group by
	mm.MakeNo, mm.MakeName ,mm.Code

--3
	select UnitTypeNo [Unit Type],null [Unit Name]
	from GlobalData.Unittype

--4
	select UnitTypeNo, UnitTypeName [Unit Type Name]
	from GlobalData.Unittype

--5

	select um.UnitNo, Alias [Unit Name]
	from masterdata.munitMaster um
	inner join masterdata.mUnitMasterCompanyDetail  umcd on umcd.UnitNo = um.UnitNo 
	left join masterdata.mSubGroupUnitDetail sd on sd.UnitNo = um.UnitNo and SubGroupNo =@SubGroupNo 
	where umcd.CompanyNo=@CompanyNo and (umcd.Inactive =0 or SubGroupNo is not null)
	group by um.UnitNo, Alias 

--6
	select null [Vendor Name], null [Location]
	where 1=2

--7
	select vm.VendorNo,Name [Vendor Name]
	from masterdata.mvendorcard vm
	inner join masterdata.mVendorCardCompanyDetail vmcd on vmcd.VendorNo = vm.VendorNo 
	left join masterdata.mSubGroupVendorDetail sd on sd.VendorNo = vm.VendorNo and SubGroupNo =@SubGroupNo 
	where vmcd.CompanyNo=@CompanyNo and (vmcd.Inactive =0 or SubGroupNo is not null)
	and VendorTypeNo in (3,6) group by vm.VendorNo,Name
	
--8
	select vl.VendorLocationNo,vl.VendorNo,FullAddress [Location]
	from masterdata.mvendorcard vm
	INNER join masterdata.mvendorLocationDetail vl on vl.VendorNo = vm.VendorNo 
	inner join masterdata.mVendorLocationDetailCompanyDetail vmcd on vmcd.VendorLocationNo = vl.VendorLocationNo 
	left join masterdata.mSubGroupVendorDetail sd on sd.VendorLocationNo = vl.VendorLocationNo
												and SubGroupNo =@SubGroupNo 
	where VendorTypeNo in (3,6) and
	vmcd.companyNO=@CompanyNo and (vmcd.Inactive =0 or SubGroupNo is not null)
	
--9
	select cm.CategoryNo,CategoryName [Category Name],[Code],CategoryName as Id
	from masterdata.mCategoryMaster cm
	inner join masterdata.mCategoryMasterCompanyDetail cmcd on cm.CategoryNo = cmcd.CategoryNo 
	where cmcd.companyNO=@CompanYNo and cmcd.Inactive =0
 
-- 10 Group Combo for fast entry

	select GM.GroupName as Id,GM.GroupName [Group Name],[GM].[Code],GM.GroupNo,GM.CategoryNo
	from masterdata.mGroupMaster GM
	Inner Join masterdata.mGroupMasterCompanyDetail GMCD
					 On GM.GroupNo = GMCD.GroupNo
	Left Join masterdata.mSubGroupMaster SGM
					On SGM.GroupNo = GM.GroupNo
					And SGM.SubGroupNo = @SubGroupNo
	Where GM.AuthorizedBy is Not Null
	And GMCD.CompanyNo = @CompanyNo
	And (GMCD.Inactive = 0 Or SGM.SubGroupNo is Not Null)
	
-- 11 Fill Fast	Entry grid

   Select '' as [Category Name], '' as [Group Name],'' as [Code],
		  '' as [Sub Group Name],'' as [Remarks]
   Where 1 = 2			   	 											 
						
-- table 12
	select GSTCategoryNo,GSTCategoryName [Category Name] from GlobalData.GSTCategory where Inactive = 0
-- table 13
	select HSNSACCodeNo ,HSNSACCode [Code],Description,t1.MiscChargeName CGST,t2.MiscChargeName SGST,t3.MiscChargeName IGST,t4.MiscChargeName UTGST 
	from GlobalData.HSNSACCode  hsn
	left join masterdata.mMiscCharges t1 on t1.MiscChargeNo = CGST
	left join masterdata.mMiscCharges t2 on t2.MiscChargeNo = SGST
	left join masterdata.mMiscCharges t3 on t3.MiscChargeNo = IGST
	left join masterdata.mMiscCharges t4 on t4.MiscChargeNo = UTGST

-- table 14
	select  distinct sg.binNo,cast(case when sgr.SubGroupNo is null then 0 else 1 end as bit) [Select]
			,sg.BinCardNo [Bin Card No.],sg.Location,Wh.WareHouseName  [WareHouse]				
	from masterdata.mBinCard sg
	inner join masterdata.mWarehouse Wh on Wh.WareHouseNo = sg.WareHouseNo 
		left join masterdata.mBinCardSubgroupDetail sgr on sgr.BinNo=sg.BinNo 
												and sgr.SubGroupNo= @SubGroupNo  
	--where sg.CompanyNo=@CompanyNo

-- Table 15 Setting
	Select DisplayDisLotTole
	from Sales.Setting
	Where CompanyNo = @CompanyNo

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















