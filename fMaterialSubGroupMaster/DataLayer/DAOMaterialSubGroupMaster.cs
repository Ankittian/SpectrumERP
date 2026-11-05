using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace SpectrumERP.DataLayer
{
    public class DAOMaterialSubGroupMaster
    {

        //Stored Procedure
        public static readonly string FillValuesDependent = "masterdata.MSGMFillValuesDependent";
        public static readonly string Validate = "masterdata.MSGMValidate";
        public static readonly string SaveDivision = "masterdata.MSGMSaveDivision";
        public static readonly string SaveMake = "masterdata.MSGMSaveMake";
        public static readonly string SaveQC = "masterdata.MSGMSaveQC";
        public static readonly string SaveUnit = "masterdata.MSGMSaveUnit";
        public static readonly string SaveVendor = "masterdata.MSGMSaveVendor";
        public static readonly string SaveMain = "masterdata.MSGMSaveMain";
        public static readonly string Delete = "masterdata.MSGMDelete";
        public static readonly string SearchData = "masterdata.MSGMSearchData";
        public static readonly string LoadData = "masterdata.MSGMLoadData";
        public static readonly string FillValues = "masterdata.MSGMFillValues";
        public static readonly string SaveBinDetail = "masterdata.MSGMSaveBinDetail";



        //variables
        public static readonly string CategoryNo = "@CategoryNo";
        public static readonly string CompanyNo = "@CompanyNo";
        public static readonly string DeductionRate = "@DeductionRate";
        public static readonly string DeductionType = "@DeductionType";
        public static readonly string DivisionNo = "@DivisionNo";
        public static readonly string DoubleDeductionFrom = "@DoubleDeductionFrom";
        public static readonly string FullSubGroupCode = "@FullSubGroupCode";
        public static readonly string GroupNo = "@GroupNo";
        public static readonly string Inactive = "@Inactive";
        public static readonly string LoginNo = "@LoginNo";
        public static readonly string MakeNo = "@MakeNo";
        public static readonly string QCParameterNo = "@QCParameterNo";
        public static readonly string ReceiptTolerance = "@ReceiptTolerance";
        public static readonly string ShipmentTolerance = "@ShipmentTolerance";
        public static readonly string StandardValue = "@StandardValue";
        public static readonly string Code = "@Code";
        public static readonly string SubGroupName = "@SubGroupName";
        public static readonly string SubGroupNo = "@SubGroupNo";
        public static readonly string ToleranceValue = "@ToleranceValue";
        public static readonly string UnitNo = "@UnitNo";
        public static readonly string UnitTypeNo = "@UnitTypeNo";
        public static readonly string VendorLocationNo = "@VendorLocationNo";
        public static readonly string VendorNo = "@VendorNo";

        public static readonly string StockValueMethodNo = "@StockValueMethodNo";
        public static readonly string WHCompanyNo = "@WHCompanyNo";
        public static readonly string WarehouseNo = "@WarehouseNo";
        //30 may 2017
        public static readonly string GSTCategoryNo = "@GSTCategoryNo";
        public static readonly string HSNSACCodeNo = "@HSNSACCodeNo";
        //16 June 2023
        public static readonly string BinNo = "@BinNo";
        //28 June 2023
        public static readonly string IsBINApplicable = "@IsBINApplicable";
        public static readonly string DispatchNegTolerance = "@DispatchNegTolerance";
    }
}
