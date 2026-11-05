using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace QCGroupdll.Datalayer
{
   public class DTQCGroup
    {
       #region private
       
        private byte bytCompanyNo;
        private short sQCGroupNo;

      #endregion
       
       # region public
       
        public byte CompanyNo
        {
            get { return bytCompanyNo; }
            set { bytCompanyNo= value; }
        }
        public short QCGroupNo
        {
            get { return sQCGroupNo; }
            set { sQCGroupNo= value; }
        }
       
     #endregion
                  
       public DataSet FillValues()
        {
           DAQCGroup objDAQCGroup = new DAQCGroup();
           return objDAQCGroup.FillValues(this);
        }
       
       public DataSet FillValuesDependent()
        {
           DAQCGroup objDAQCGroup = new DAQCGroup();
           return objDAQCGroup.FillValuesDependent(this);
        }


   }
}
