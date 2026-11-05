using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace SpectrumERP.DataLayer
{
    public class DAOUnitMaster
    {
    
       //Stored Procedure
       public static readonly string Validate = "masterdata.MMUMValidate";
       public static readonly string Delete = "masterdata.MMUMDelete";
       public static readonly string SearchData = "masterdata.MMUMSearchData";
       public static readonly string Save = "masterdata.MMUMSave";
       public static readonly string SaveUnitConversionDetail = "masterdata.MMUMSaveUnitConversionDetail";
       public static readonly string LoadData = "masterdata.MMUMLoadData";
       public static readonly string SaveSubGroupUnitDetail = "masterdata.MMUMSaveSubGroupUnitDetail";
       public static readonly string FillValues = "masterdata.MMUMFillValues";


       //variables
        public static readonly string Alias = "@Alias";
     
        public static readonly string CompanyNo = "@CompanyNo";
        public static readonly string ConversionType = "@ConversionType";
        public static readonly string ConversionUnitNo = "@ConversionUnitNo";
        public static readonly string FirstCF = "@FirstCF";
        public static readonly string Inactive = "@Inactive";
        public static readonly string LoginNo = "@LoginNo";
        public static readonly string SecondCF = "@SecondCF";
        public static readonly string SubGroupNo = "@SubGroupNo";
        public static readonly string UnitCategoryNo = "@UnitCategoryNo";
        public static readonly string UnitName = "@UnitName";
        public static readonly string UnitNo = "@UnitNo";
        public static readonly string UnitTypeNo = "@UnitTypeNo";
        public static readonly string GSTUQC = "@GSTUQC";
   }
}
