using System;
using System.Data;
using System.Collections.Generic;
using System.Text;

namespace SpectrumERP.DataLayer
{
    public class DAMaterialGroup
    {
        public DataSet LoadData(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.GroupNo,ODTMaterialGroup.GroupNo );
            dicPara.Add(DAOMaterialGroup.CompanyNo, ODTMaterialGroup.CompanyNo);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.LoadData, dicPara);
        }
        public DataSet Delete(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.GroupNo,ODTMaterialGroup.GroupNo );
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.Delete, dicPara);
        }
        public DataSet FillValuesDependent(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.CategoryNo,ODTMaterialGroup.CategoryNo );
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.FillValuesDependent, dicPara);
        }
        public DataSet FillValues(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.CompanyNo,ODTMaterialGroup.CompanyNo );
            dicPara.Add(DAOMaterialGroup.GroupNo, ODTMaterialGroup.GroupNo);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.FillValues, dicPara);
        }
        public DataSet Save(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.GroupNo,ODTMaterialGroup.GroupNo );
            dicPara.Add(DAOMaterialGroup.CategoryNo,ODTMaterialGroup.CategoryNo );

            dicPara.Add(DAOMaterialGroup.GroupCode,ODTMaterialGroup.GroupCode );
            dicPara.Add(DAOMaterialGroup.GroupName,ODTMaterialGroup.GroupName );

            dicPara.Add(DAOMaterialGroup.LoginNo,ODTMaterialGroup.LoginNo );
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.Save, dicPara);
        }
        public DataSet SaveQCParameter(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.GroupNo,ODTMaterialGroup.GroupNo );
            dicPara.Add(DAOMaterialGroup.QCParameterNo,ODTMaterialGroup.QCParameterNo );

            dicPara.Add(DAOMaterialGroup.StandardValue,ODTMaterialGroup.StandardValue );
            dicPara.Add(DAOMaterialGroup.ToleranceValue,ODTMaterialGroup.ToleranceValue );

            dicPara.Add(DAOMaterialGroup.DeductionRate,ODTMaterialGroup.DeductionRate );
            dicPara.Add(DAOMaterialGroup.DeductionType,ODTMaterialGroup.DeductionType );

            dicPara.Add(DAOMaterialGroup.DoubleDeductionFrom,ODTMaterialGroup.DoubleDeductionFrom );
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.SaveQCParameter, dicPara);
        }
        public DataSet SearchData(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.CompanyNo,ODTMaterialGroup.CompanyNo );
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.SearchData, dicPara);
        }

        public DataSet Validate(DTMaterialGroup ODTMaterialGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOMaterialGroup.GroupName , ODTMaterialGroup.GroupName );
            dicPara.Add(DAOMaterialGroup.GroupNo , ODTMaterialGroup.GroupNo );

            dicPara.Add(DAOMaterialGroup.CategoryNo, ODTMaterialGroup.CategoryNo);
            dicPara.Add(DAOMaterialGroup.CompanyNo, ODTMaterialGroup.CompanyNo);
            dicPara.Add(DAOMaterialGroup.GroupCode, ODTMaterialGroup.GroupCode);
            return LocalVariables.objBase.ExecuteProc(DAOMaterialGroup.Validate, dicPara);
        }
    }
}
