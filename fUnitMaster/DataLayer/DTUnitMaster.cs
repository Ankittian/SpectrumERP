using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace SpectrumERP.DataLayer
{
    public class DTUnitMaster
    {
       #region private


        private bool bInactive;
        private byte btCompanyNo;
        private byte btConversionType;
        private byte btUnitCategoryNo;
        private byte btUnitTypeNo;
       
        private double dFirstCF;
        private double dSecondCF;
        private int iLoginNo;
        private short sConversionUnitNo;
        private short sSubGroupNo;
        private string strAlias;
        private string strUnitName;
        private short sUnitNo;
        private Nullable<int> iGSTUQC;

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
        public byte ConversionType
        {
            get { return btConversionType; }
            set { btConversionType= value; }
        }
        public byte UnitCategoryNo
        {
            get { return btUnitCategoryNo; }
            set { btUnitCategoryNo= value; }
        }
        public byte UnitTypeNo
        {
            get { return btUnitTypeNo; }
            set { btUnitTypeNo= value; }
        }
      
        public double FirstCF
        {
            get { return dFirstCF; }
            set { dFirstCF= value; }
        }
        public double SecondCF
        {
            get { return dSecondCF; }
            set { dSecondCF= value; }
        }
        public int LoginNo
        {
            get { return iLoginNo; }
            set { iLoginNo= value; }
        }
      
        public short ConversionUnitNo
        {
            get { return sConversionUnitNo; }
            set { sConversionUnitNo= value; }
        }
        public short SubGroupNo
        {
            get { return sSubGroupNo; }
            set { sSubGroupNo= value; }
        }
        public string Alias
        {
            get { return strAlias; }
            set { strAlias= value; }
        }
        public string UnitName
        {
            get { return strUnitName; }
            set { strUnitName= value; }
        }
        public short UnitNo
        {
            get { return sUnitNo; }
            set { sUnitNo= value; }
        }
        public Nullable<int> GSTUQC
        {
            get { return iGSTUQC; }
            set { iGSTUQC = value; }
        }

     #endregion


       public DataSet Validate()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.Validate(this);
        }


       public DataSet Delete()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.Delete(this);
        }


       public DataSet SearchData()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.SearchData(this);
        }


       public DataSet Save()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.Save(this);
        }


       public DataSet SaveUnitConversionDetail()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.SaveUnitConversionDetail(this);
        }


       public DataSet LoadData()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.LoadData(this);
        }


       public DataSet SaveSubGroupUnitDetail()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.SaveSubGroupUnitDetail(this);
        }


       public DataSet FillValues()
        {
           DAUnitMaster objDAUnitMaster = new DAUnitMaster();
           return objDAUnitMaster.FillValues(this);
        }


   }
}
