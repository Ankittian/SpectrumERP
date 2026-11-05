using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace SpectrumERP.DataLayer
{
    public class DTMaterialGroup
    {
       #region private


        private bool bInactive;
        private byte btCompanyNo;
        private byte btDeductionRate;
        private byte btDeductionType;
        private Nullable<double> dDoubleDeductionFrom;
        private double dStandardValue;
        private double dToleranceValue;
        private int iLoginNo;
        private short sCategoryNo;
        private short droupNo;
        private short sQCParameterNo;
        private string strGroupCode;
        private string strGroupName;


      #endregion


       # region public


        public bool Inactive
        {
            get { return bInactive; }
            set { bInactive= value; }
        }
        public byte CompanyNo
        {
            get { return btCompanyNo; }
            set { btCompanyNo= value; }
        }
        public byte DeductionRate
        {
            get { return btDeductionRate; }
            set { btDeductionRate= value; }
        }
        public byte DeductionType
        {
            get { return btDeductionType; }
            set { btDeductionType= value; }
        }
        public Nullable<double> DoubleDeductionFrom
        {
            get { return dDoubleDeductionFrom; }
            set { dDoubleDeductionFrom= value; }
        }
        public double StandardValue
        {
            get { return dStandardValue; }
            set { dStandardValue= value; }
        }
        public double ToleranceValue
        {
            get { return dToleranceValue; }
            set { dToleranceValue= value; }
        }
       
        public int LoginNo
        {
            get { return iLoginNo; }
            set { iLoginNo= value; }
        }
        public short CategoryNo
        {
            get { return sCategoryNo; }
            set { sCategoryNo= value; }
        }
        public short GroupNo
        {
            get { return droupNo; }
            set { droupNo= value; }
        }
        public short QCParameterNo
        {
            get { return sQCParameterNo; }
            set { sQCParameterNo= value; }
        }
        public string GroupCode
        {
            get { return strGroupCode; }
            set { strGroupCode= value; }
        }
        public string GroupName
        {
            get { return strGroupName; }
            set { strGroupName= value; }
        }


     #endregion


       public DataSet LoadData()
        {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.LoadData(this);
        }


       public DataSet Delete()
        {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.Delete(this);
        }


       public DataSet FillValuesDependent()
        {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.FillValuesDependent(this);
        }


       public DataSet FillValues()
        {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.FillValues(this);
        }


       public DataSet Save()
        {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.Save(this);
        }


       public DataSet SaveQCParameter()
        {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.SaveQCParameter(this);
        }


       public DataSet SearchData()
        {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.SearchData(this);
        }

       public DataSet Validate()
       {
           DAMaterialGroup objDAMaterialGroup = new DAMaterialGroup();
           return objDAMaterialGroup.Validate(this);
       }


   }
}
