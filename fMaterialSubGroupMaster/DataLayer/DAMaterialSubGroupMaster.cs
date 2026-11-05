using System;
using System.Data;
using System.Collections.Generic;
using System.Text;

namespace SpectrumERP.DataLayer
{
    public class DAMaterialSubGroupMaster
    {
        public DataSet FillValuesDependent(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.CategoryNo, ODTMaterialSubGroupMaster.CategoryNo);
            dicPara.Add(DAOMaterialSubGroupMaster.GroupNo, ODTMaterialSubGroupMaster.GroupNo);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.FillValuesDependent, dicPara);
        }
        public DataSet Validate(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);
            dicPara.Add(DAOMaterialSubGroupMaster.FullSubGroupCode, ODTMaterialSubGroupMaster.FullSubGroupCode);

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.GroupNo, ODTMaterialSubGroupMaster.GroupNo);

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupName, ODTMaterialSubGroupMaster.SubGroupName);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.Validate, dicPara);
        }
        public DataSet SaveDivision(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.DivisionNo, ODTMaterialSubGroupMaster.DivisionNo);
            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);

            dicPara.Add(DAOMaterialSubGroupMaster.WHCompanyNo, ODTMaterialSubGroupMaster.WHCompanyNo);
            dicPara.Add(DAOMaterialSubGroupMaster.WarehouseNo, ODTMaterialSubGroupMaster.WarehouseNo);

            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SaveDivision, dicPara);
        }
        public DataSet SaveMake(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.MakeNo, ODTMaterialSubGroupMaster.MakeNo);

            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);

            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SaveMake, dicPara);
        }
        public DataSet SaveQC(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.QCParameterNo, ODTMaterialSubGroupMaster.QCParameterNo);

            dicPara.Add(DAOMaterialSubGroupMaster.StandardValue, ODTMaterialSubGroupMaster.StandardValue);
            dicPara.Add(DAOMaterialSubGroupMaster.ToleranceValue, ODTMaterialSubGroupMaster.ToleranceValue);

            dicPara.Add(DAOMaterialSubGroupMaster.DeductionRate, ODTMaterialSubGroupMaster.DeductionRate);
            dicPara.Add(DAOMaterialSubGroupMaster.DeductionType, ODTMaterialSubGroupMaster.DeductionType);

            dicPara.Add(DAOMaterialSubGroupMaster.DoubleDeductionFrom, ODTMaterialSubGroupMaster.DoubleDeductionFrom);
            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);

            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SaveQC, dicPara);
        }
        public DataSet SaveUnit(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.UnitTypeNo, ODTMaterialSubGroupMaster.UnitTypeNo);

            dicPara.Add(DAOMaterialSubGroupMaster.UnitNo, ODTMaterialSubGroupMaster.UnitNo);
            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);

            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SaveUnit, dicPara);
        }
        public DataSet SaveVendor(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.VendorNo, ODTMaterialSubGroupMaster.VendorNo);

            dicPara.Add(DAOMaterialSubGroupMaster.VendorLocationNo, ODTMaterialSubGroupMaster.VendorLocationNo);
            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);

            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SaveVendor, dicPara);
        }
        public DataSet SaveMain(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.GroupNo, ODTMaterialSubGroupMaster.GroupNo);

            dicPara.Add(DAOMaterialSubGroupMaster.Code, ODTMaterialSubGroupMaster.Code);
            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupName, ODTMaterialSubGroupMaster.SubGroupName);

            dicPara.Add(DAOMaterialSubGroupMaster.ReceiptTolerance, ODTMaterialSubGroupMaster.ReceiptTolerance);
            dicPara.Add(DAOMaterialSubGroupMaster.ShipmentTolerance, ODTMaterialSubGroupMaster.ShipmentTolerance);

            dicPara.Add(DAOMaterialSubGroupMaster.LoginNo, ODTMaterialSubGroupMaster.LoginNo);
            dicPara.Add(DAOMaterialSubGroupMaster.GSTCategoryNo, ODTMaterialSubGroupMaster.GSTCategoryNo);

            dicPara.Add(DAOMaterialSubGroupMaster.HSNSACCodeNo, ODTMaterialSubGroupMaster.HSNSACCodeNo);
            dicPara.Add(DAOMaterialSubGroupMaster.IsBINApplicable, ODTMaterialSubGroupMaster.IsBINApplicable);

            dicPara.Add(DAOMaterialSubGroupMaster.DispatchNegTolerance, ODTMaterialSubGroupMaster.DispatchNegTolerance);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SaveMain, dicPara);
        }
        public DataSet Delete(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.Delete, dicPara);
        }
        public DataSet SearchData(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SearchData, dicPara);
        }
        public DataSet LoadData(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);

            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.LoadData, dicPara);
        }
        public DataSet FillValues(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.CompanyNo, ODTMaterialSubGroupMaster.CompanyNo);
            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.FillValues, dicPara);
        }
        public DataSet SaveBinDetail(DTMaterialSubGroupMaster ODTMaterialSubGroupMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialSubGroupMaster.SubGroupNo, ODTMaterialSubGroupMaster.SubGroupNo);
            dicPara.Add(DAOMaterialSubGroupMaster.BinNo, ODTMaterialSubGroupMaster.BinNo);

            return LocalVariables.objBase.ExecuteProc(DAOMaterialSubGroupMaster.SaveBinDetail, dicPara);
        }
    }
}
