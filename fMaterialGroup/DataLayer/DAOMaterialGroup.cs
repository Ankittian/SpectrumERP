using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace SpectrumERP.DataLayer
{
    public class DAOMaterialGroup
    {
    
       //Stored Procedure
       public static readonly string LoadData = "masterdata.MMIGLoadData";
       public static readonly string Delete = "masterdata.MMIGDelete";
       public static readonly string FillValuesDependent = "masterdata.MMIGFillValuesDependent";
       public static readonly string FillValues = "masterdata.MMIGFillValues";
       public static readonly string Save = "masterdata.MMIGSave";
       public static readonly string SaveQCParameter = "masterdata.MMIGSaveQCParameter";
       public static readonly string SearchData = "masterdata.MMIGSearchData";
       public static readonly string Validate = "[masterdata].[MMIGValidate]";

       //variables
        public static readonly string CategoryNo = "@CategoryNo";
        public static readonly string CompanyNo = "@CompanyNo";
        public static readonly string DeductionRate = "@DeductionRate";
        public static readonly string DeductionType = "@DeductionType";
        public static readonly string DoubleDeductionFrom = "@DoubleDeductionFrom";
        public static readonly string GroupCode = "@GroupCode";
        public static readonly string GroupName = "@GroupName";
        public static readonly string GroupNo = "@GroupNo";
        public static readonly string Inactive = "@Inactive";
        public static readonly string LoginNo = "@LoginNo";
        public static readonly string QCParameterNo = "@QCParameterNo";
        public static readonly string StandardValue = "@StandardValue";
        public static readonly string ToleranceValue = "@ToleranceValue";
   }
}
