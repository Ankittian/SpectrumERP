using System;
using System.Data;
using System.Collections.Generic;
using System.Text;

namespace SpectrumERP.DataLayer
{
    public class DAUnitMaster
    {
        public DataSet Validate(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.UnitName,ODTUnitMaster.UnitName );
            dicPara.Add(DAOUnitMaster.UnitNo,ODTUnitMaster.UnitNo );

            dicPara.Add(DAOUnitMaster.CompanyNo,ODTUnitMaster.CompanyNo );
            dicPara.Add(DAOUnitMaster.Alias,ODTUnitMaster.Alias );

            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.Validate, dicPara);
        }
        public DataSet Delete(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.UnitNo,ODTUnitMaster.UnitNo );
            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.Delete, dicPara);
        }
        public DataSet SearchData(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.CompanyNo,ODTUnitMaster.CompanyNo );
            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.SearchData, dicPara);
        }
        public DataSet Save(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.UnitNo,ODTUnitMaster.UnitNo );
            dicPara.Add(DAOUnitMaster.UnitName,ODTUnitMaster.UnitName );

            dicPara.Add(DAOUnitMaster.Alias,ODTUnitMaster.Alias );
            dicPara.Add(DAOUnitMaster.UnitCategoryNo,ODTUnitMaster.UnitCategoryNo );

            dicPara.Add(DAOUnitMaster.LoginNo,ODTUnitMaster.LoginNo );
            dicPara.Add(DAOUnitMaster.GSTUQC, ODTUnitMaster.GSTUQC);
            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.Save, dicPara);
        }

        public DataSet SaveUnitConversionDetail(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.UnitNo,ODTUnitMaster.UnitNo );
            dicPara.Add(DAOUnitMaster.ConversionType,ODTUnitMaster.ConversionType );

            dicPara.Add(DAOUnitMaster.FirstCF,ODTUnitMaster.FirstCF );
            dicPara.Add(DAOUnitMaster.SecondCF,ODTUnitMaster.SecondCF );

            dicPara.Add(DAOUnitMaster.ConversionUnitNo,ODTUnitMaster.ConversionUnitNo );
            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.SaveUnitConversionDetail, dicPara);
        }
        public DataSet LoadData(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.UnitNo,ODTUnitMaster.UnitNo );
            dicPara.Add(DAOUnitMaster.CompanyNo, ODTUnitMaster.CompanyNo);
            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.LoadData, dicPara);
        }
        public DataSet SaveSubGroupUnitDetail(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.UnitNo,ODTUnitMaster.UnitNo );
            dicPara.Add(DAOUnitMaster.SubGroupNo,ODTUnitMaster.SubGroupNo );

            dicPara.Add(DAOUnitMaster.UnitTypeNo,ODTUnitMaster.UnitTypeNo );
            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.SaveSubGroupUnitDetail, dicPara);
        }
        public DataSet FillValues(DTUnitMaster ODTUnitMaster)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOUnitMaster.CompanyNo,ODTUnitMaster.CompanyNo );
            dicPara.Add(DAOUnitMaster.UnitNo,ODTUnitMaster.UnitNo );

            return LocalVariables.objBase.ExecuteProc(DAOUnitMaster.FillValues, dicPara);
        }
    }
}
