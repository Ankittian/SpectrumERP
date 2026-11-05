using System;
using System.Data;
using System.Collections.Generic;
using System.Text;

namespace QCGroupdll.Datalayer
{
    public class DAQCGroup
    {
        public DataSet FillValues(DTQCGroup ODTQCGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOQCGroup.CompanyNo,ODTQCGroup.CompanyNo );

            return LocalVariables.objBase.ExecuteProc(DAOQCGroup.FillValues, dicPara);
        }
        public DataSet FillValuesDependent(DTQCGroup ODTQCGroup)
        {
            Dictionary<string, object> dicPara = new Dictionary<string, object>();

            dicPara.Add(DAOQCGroup.QCGroupNo,ODTQCGroup.QCGroupNo );
            dicPara.Add(DAOQCGroup.CompanyNo, ODTQCGroup.CompanyNo);
            
            return LocalVariables.objBase.ExecuteProc(DAOQCGroup.FillValuesDependent, dicPara);
        }
    }
}
