using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace QCGroupdll.Datalayer
{
    class DAOQCGroup
    {
    
       //Stored Procedure
       public static readonly string FillValues = "masterdata.QCFillValues";
       public static readonly string FillValuesDependent = "masterdata.QCFillValuesDependent";


       //variables
        public static readonly string CompanyNo = "@CompanyNo";
        public static readonly string QCGroupNo = "@QCGroupNo";
   }
}
